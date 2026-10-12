# SCENERYX OPEN SOURCE NOTICES & THIRD-PARTY LICENSES

**Last Updated: October 2026**  
**Publisher:** Sidestick Priority  
**Software:** SceneryX (Desktop Application for Microsoft Windows)

SceneryX is built with the assistance of several high-quality open source libraries and runtime interfaces. In compliance with the licensing terms of these respective open source projects, the copyright notices, permission notices, and disclaimers are reproduced below.

---

### 1. Leaflet.js
**Component:** Interactive Map Rendering & Geospatial Vector Layers  
**License:** BSD 2-Clause License  
**Copyright:** Copyright (c) 2010-2024, Vladimir Agafonkin; Copyright (c) 2010-2011, CloudMade.

```text
Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

### 2. pywebview
**Component:** Native Desktop Webview Host Architecture  
**License:** BSD 3-Clause License  
**Copyright:** Copyright (c) 2014-2024, Roman Sirokov and contributors.

```text
Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

### 3. Tailwind CSS
**Component:** Utility-First CSS Framework & Design System Tokens  
**License:** MIT License  
**Copyright:** Copyright (c) Tailwind Labs, Inc.

```text
MIT License

Copyright (c) Tailwind Labs, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

### 4. Microsoft Flight Simulator SimConnect API
**Component:** Real-Time Flight Telemetry & Sim State Synchronization  
**Compliance Notice:** Dynamic Linking & Non-Redistribution Notice

SceneryX integrates with Microsoft Flight Simulator via the official **SimConnect SDK API**. 
- SceneryX connects through standard dynamic linking (`SimConnect.dll` located in the Windows operating system runtime / official simulator directory).
- **No proprietary Microsoft binary files, redistributable packages, or copyrighted SDK DLLs are bundled or redistributed inside the `SceneryX.exe` binary.**
- SimConnect and Microsoft Flight Simulator are registered trademarks of Microsoft Corporation.

---

### 5. Font Awesome Free
**Component:** Cockpit Icons & User Interface Glyphs  
**License:** Font Awesome Free License (CC BY 4.0 / SIL OFL 1.1 / MIT License)  
**Copyright:** Copyright (c) Fonticons, Inc.

The icons used in SceneryX are licensed under the Creative Commons Attribution 4.0 International license (Icons), the SIL OFL 1.1 license (Fonts), and the MIT License (Code).

---

### 6. Additional Open Source Python Packages
The following Python modules and dependencies used in the SceneryX build are acknowledged with appreciation:
- **psutil:** BSD 3-Clause License (Copyright (c) 2009, Jay Loden, Dave Daeschler, Giampaolo Rodola).
- **pystray:** LGPL / GPL License (Windows System Tray integration).
- **Pillow (PIL Fork):** Historical HPND-style License (Copyright (c) 2010-2024 Alex Clark and contributors).
- **Rich & Pygments:** MIT & BSD 2-Clause Licenses (Diagnostic and console logging).
