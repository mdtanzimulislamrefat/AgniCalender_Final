import csv
import io
import unittest

from backend.processing.harmonize import (
    build_calendar, harmonize_events, monthly_calendar, normalize_row, parse_csv,
)


def archive_csv(*changes, instrument='VIIRS'):
    base = dict(latitude='23', longitude='90', brightness='330', scan='0.4', track='0.6',
                acq_date='2023-04-10', acq_time='0745', satellite='N', instrument=instrument,
                confidence='n', version='2', bright_t31='300', frp='5', daynight='D', type='0')
    if instrument == 'MODIS':
        base |= dict(satellite='Aqua', confidence='80', version='61.03')
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(base))
    writer.writeheader()
    for change in changes:
        writer.writerow(base | change)
    return output.getvalue().encode()


def event(date, sensors=('VIIRS',), max_frp=5.0):
    return {'date': date, 'latitude': 23.0, 'longitude': 90.0, 'sensors': list(sensors),
            'satellites': ['N'], 'detection_count': 1, 'n_pixels': 1,
            'frp_by_sensor_mw': {}, 'max_frp_mw': max_frp, 'daynight': ['D'],
            'first_seen_utc': date + 'T07:45:00+00:00', 'last_seen_utc': date + 'T07:45:00+00:00'}


class HarmonizeTests(unittest.TestCase):
    def test_same_fire_modis_and_viirs_same_day_merges_to_one_event(self):
        # parse_csv takes one source per file, so parse each sensor file separately.
        viirs, _ = parse_csv(archive_csv({}), 'VIIRS_SNPP_ARCHIVE')
        modis, _ = parse_csv(archive_csv(
            {'instrument': 'MODIS', 'satellite': 'Aqua', 'confidence': '80', 'version': '61.03',
             'latitude': '23.005', 'longitude': '90.005', 'acq_time': '1330', 'frp': '40'},
        ), 'MODIS_ARCHIVE')
        events, other = harmonize_events(viirs + modis)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['sensors'], ['MODIS', 'VIIRS'])
        self.assertEqual(events[0]['detection_count'], 2)
        self.assertEqual(events[0]['n_pixels'], 2)
        self.assertEqual(other, {})

    def test_two_fires_5km_apart_stay_separate(self):
        records, _ = parse_csv(archive_csv(
            {}, {'latitude': '23.05', 'longitude': '90.0', 'acq_time': '1345'}), 'VIIRS_SNPP_ARCHIVE')
        events, _ = harmonize_events(records)
        self.assertEqual(len(events), 2)

    def test_same_location_different_days_stays_separate(self):
        records, _ = parse_csv(archive_csv(
            {}, {'acq_date': '2023-04-11', 'acq_time': '0745'}), 'VIIRS_SNPP_ARCHIVE')
        events, _ = harmonize_events(records)
        self.assertEqual(len(events), 2)
        self.assertEqual([e['date'] for e in events], ['2023-04-10', '2023-04-11'])

    def test_non_vegetation_types_excluded_but_counted_separately(self):
        records, _ = parse_csv(archive_csv(
            {}, {'type': '2', 'acq_time': '0800'}, {'type': '3', 'acq_time': '0815'},
            {'type': '1', 'acq_time': '0830'}), 'VIIRS_SNPP_ARCHIVE')
        events, other = harmonize_events(records)
        self.assertEqual(len(events), 1)  # only the type-0 detection becomes an event
        self.assertEqual(other, {'static_land': 1, 'offshore': 1, 'volcano': 1})

    def test_frp_is_never_summed_across_sensors(self):
        viirs, _ = parse_csv(archive_csv({'frp': '50'}), 'VIIRS_SNPP_ARCHIVE')
        modis, _ = parse_csv(archive_csv(
            {'instrument': 'MODIS', 'satellite': 'Aqua', 'confidence': '80', 'version': '61.03',
             'latitude': '23.005', 'longitude': '90.005', 'acq_time': '1330', 'frp': '100'},
        ), 'MODIS_ARCHIVE')
        events, _ = harmonize_events(viirs + modis)
        self.assertEqual(len(events), 1)
        by_sensor = events[0]['frp_by_sensor_mw']
        self.assertEqual(by_sensor['MODIS']['max_mw'], 100)
        self.assertEqual(by_sensor['VIIRS']['max_mw'], 50)
        self.assertEqual(events[0]['max_frp_mw'], 100)  # max, not 100 + 50 = 150
        self.assertNotIn('frp_sum_mw', events[0])
        self.assertNotIn('total_frp_mw', events[0])

    def test_climatology_anomaly_and_critical_flag(self):
        # April: 10 events in 2023, 10 in 2024, 40 in 2025 -> mean 20, std ~17.3,
        # 2025-04 anomaly z ~ +1.15 and critical (40 > 20 + 17.3).
        events = ([event(f'2023-04-{d:02d}') for d in range(1, 11)]
                  + [event(f'2024-04-{d:02d}') for d in range(1, 11)]
                  + [event(f'2025-04-{d:02d}') for d in range(1, 11)]
                  + [event('2025-04-11'), event('2025-04-12'), event('2025-04-13')]
                  + [event(f'2025-04-{d:02d}') for d in range(14, 41)])
        rows = monthly_calendar(events, [], [2023, 2024, 2025], [2023, 2024, 2025])
        apr25 = next(r for r in rows if r['year_month'] == '2025-04')
        self.assertEqual(apr25['harmonized_event_count'], 40)
        self.assertAlmostEqual(apr25['climatology_mean'], 20.0)
        self.assertAlmostEqual(apr25['anomaly_z'], 1.15, places=1)
        self.assertTrue(apr25['critical'])
        apr23 = next(r for r in rows if r['year_month'] == '2023-04')
        self.assertFalse(apr23['critical'])
        # A month with no events in a covered year counts as 0, not missing.
        jan23 = next(r for r in rows if r['year_month'] == '2023-01')
        self.assertEqual(jan23['harmonized_event_count'], 0)

    def test_build_calendar_carries_method_and_limitations(self):
        records, _ = parse_csv(archive_csv({}), 'VIIRS_SNPP_ARCHIVE')
        doc = build_calendar(records, [2023], {'VIIRS_SNPP_ARCHIVE': [2023]})
        self.assertEqual(doc['totals']['harmonized_events'], 1)
        self.assertEqual(doc['totals']['raw_detections'], 1)
        self.assertIn('1.0 km', doc['method']['clustering'])
        self.assertTrue(doc['limitations'])
        self.assertEqual(doc['coverage']['complete_years_for_climatology'], [2023])

    def test_invalid_rows_are_counted_not_guessed(self):
        _, stats = parse_csv(archive_csv({'latitude': 'nan'}, {'acq_time': '2460'}, {}),
                             'VIIRS_SNPP_ARCHIVE')
        self.assertEqual(stats['invalid'], 2)
        self.assertEqual(stats['retained'], 1)
        with self.assertRaises(ValueError):
            parse_csv(b'<html>Service unavailable</html>', 'VIIRS_SNPP_ARCHIVE')


if __name__ == '__main__':
    unittest.main()
