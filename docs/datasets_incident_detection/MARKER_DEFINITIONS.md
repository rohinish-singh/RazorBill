# CP2 behavioral marker definitions

All outputs are observations with `status: needs_review`; none is a finding of criminal intent or malicious tampering.

| Marker | Trigger | Shared category | Key evidence / limitations |
|---|---|---|---|
| `restricted_zone_entry` | A confirmed person track footpoint crosses into a configured restricted polygon. One alert per continuous entry plus cooldown. | `suspicious_activity` | Zone ID and footpoint. A zone crossing alone does not establish intent. |
| `loitering` | A track remains in a configured zone beyond a threshold with enough observations. Track loss resets state; a changed ID is not linked. | `suspicious_activity` | Observed dwell duration and count. It does not claim suspicious behavior. |
| `crowd_gathering` | Distinct person tracks meet a zone count threshold for a sustained interval. | `crowd_incident` | Track count, zone, persistence. It is density/activity only. |
| `camera_dark` | Low mean luminance is sustained; evidence notes whether the preceding sample had an abrupt drop. | `other` | Luminance and transition flag. Natural lighting can cause it. |
| `camera_obstruction_candidate` | Low sharpness and texture persist. | `other` | Sharpness/texture plus autofocus/weather/lighting caveat. |
| `frozen_feed_candidate` | Consecutive frames have a very low mean absolute difference for a conservative interval. | `other` | Difference and static-scene caveat. |
| `source_read_failure` | The ingestion owner explicitly signals failure. | `other` | Decoder/source reason only. |

Marker types are carried in `trigger` and evidence notes because `SHARED_CONTRACTS.md` has no dedicated camera-health category. Person 3/4 must approve any display/API treatment before integration.
