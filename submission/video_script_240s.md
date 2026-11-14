# 240-second video outline — Bangladesh local pitch (4 minutes)

Bangladesh local organisers mentioned a 240-second (4-minute) video in one post.
Use this for the **local** pitch if your Dhaka judges ask for it. The **global**
demo link stays the 30-second video (see video_script_30s.md) or the 7 slides.

Total 4:00. English, with Bangla subtitles optional. Screen-record the web demo;
film the team for at most 30 seconds total (intro + closing).

| Time | Section | On screen / say |
|---|---|---|
| 0:00–0:20 | Hook | Team on camera, one line each: "In Bangladesh, March and April burn every year. But nobody could say how much — because every satellite counted the same fire again." Cut to hero. |
| 0:20–0:50 | Problem | Raw counts by sensor, side by side. "MODIS says one number, VIIRS says three times that. Same fires. Different pixels. Counting pixels is not counting fires." Show 2012→2013 jump (2,862 → 7,411). |
| 0:50–1:30 | Method | Diagram: three sensor dots → one event circle (1 km / same day). "Vegetation fires only. Same day, within one kilometre, one event. FRP never summed across sensors. That is the whole harmonization — simple enough to check, honest enough to trust." Show method note. |
| 1:30–2:20 | Results | Heatmap 2003–2024. "244,308 detections. 117,602 events. Peak: April 2023, 4,746 events. March–April is the season in all 22 years." Yearly raw-vs-harmonized bars. |
| 2:20–3:10 | Critical periods | Critical table. "January 2019: 1,097 events, almost double its average. June 2023: only 83 events — but June averages 39. Small number, big warning. That is what early warning looks like: unusual for its month, not just big." |
| 3:10–3:40 | Who uses it | "A fire service officer checks March before the season. A researcher compares Aprils, not pixels. A farmer near the Sundarbans fringe sees when the risk window opens." Show saved-area / map in the Android app briefly. |
| 3:40–4:00 | Limits + close | "2025 is not in yet — NASA has not published it. Six climatology years, so critical means check it, not panic. Code, data and method are all in the repo. AgniCalendar — one fire calendar for Bangladesh." End card: repo URL + demo URL. |

Keep every number exactly as in `web/data/harmonized.json` / `HARMONIZATION_METHOD.md`.
Do not add a number that is not in those files.
