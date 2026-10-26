# T09 implementation evidence

Viewer: wheel/pinch zoom at cursor, drag pan; real units at20%, icons below18% with hysteresis. Text uses screen coordinates, font readiness and DPR<=2. Pixel sprites retain nearest filtering. Tank visual travel180ms/trail300ms; artillery follows recorded timing with tangent/trail; offscreen source arrows are cosmetic. Engine damage timing is unchanged by viewer.

`browser.json` and screenshots: synthetic 128 infantry/20 vehicle scene, DPR1/2 and zoom6/18/19/20/35/65; desktop1440x900, tablet1024x768, mobile390x844. Actual Mac input is unverified. JS25/build pass. Training stopped safely at2090 and preserved before engine changes. Latest actual replay seed39 had BLOCKED91/TRAFFIC_TIMEOUT10; this is one game, not the user's identified match.

GitHub Release upload actually returned HTTP401. Code push and API read authentication do not establish asset upload authentication. Pending models must not be deleted.
