import os
import webbrowser
import folium
from folium.plugins import LocateControl, MiniMap

# --- CẤU HÌNH DỮ LIỆU ---
VIETNAM_CENTER = [16.047079, 108.206230]
INITIAL_ZOOM = 6

TILE_LAYERS = [
    {
        "url": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "attr": "Google Maps",
        "name": "Google Maps (Đường xá)",
        "max_zoom": 20,
    },
    {
        "url": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "attr": "Google Maps Satellite",
        "name": "Google Hybrid (Vệ tinh + Tên đường)",
        "max_zoom": 20,
    },
    {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles &copy; Esri",
        "name": "Vệ tinh Esri (Nhà cửa chi tiết)",
        "max_zoom": 18,
    },
]

LOCATIONS = [
    {"name": "Thủ đô Hà Nội", "loc": [21.028511, 105.804817], "color": "red"},
    {"name": "TP. Hồ Chí Minh", "loc": [10.823099, 106.629664], "color": "blue"},
    {"name": "TP. Đà Nẵng", "loc": [16.047079, 108.206230], "color": "green"},
    {"name": "Quần đảo Hoàng Sa (Việt Nam)", "loc": [16.5, 112.0], "color": "orange"},
    {"name": "Quần đảo Trường Sa (Việt Nam)", "loc": [8.65, 111.92], "color": "orange"},
]


def build_vietnam_routing_map(output_filename="index.html"):
    # 1. Khởi tạo bản đồ
    m = folium.Map(
        location=VIETNAM_CENTER,
        zoom_start=INITIAL_ZOOM,
        tiles=None,
        prefer_canvas=True,
        rotate=True,
        touchRotate=True,
        bearing=0
    )

    # Thêm CDN Leaflet.Rotate & Viewport Meta tag cho Mobile
    head_html = '''
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <script src="https://cdn.jsdelivr.net/npm/leaflet-rotate@0.2.8/dist/leaflet-rotate-src.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-rotate@0.2.8/dist/leaflet-rotate.css" />
    '''
    m.get_root().header.add_child(folium.Element(head_html))

    # 2. Thêm các Lớp bản đồ
    for layer in TILE_LAYERS:
        folium.TileLayer(
            tiles=layer["url"],
            attr=layer["attr"],
            name=layer["name"],
            max_zoom=layer["max_zoom"]
        ).add_to(m)

    # 3. Marker các thành phố chính
    markers_group = folium.FeatureGroup(name="Thành phố chính").add_to(m)
    for item in LOCATIONS:
        folium.Marker(
            location=item["loc"],
            popup=folium.Popup(f"<b>{item['name']}</b>", max_width=300),
            tooltip=item["name"],
            icon=folium.Icon(color=item["color"], icon="info-sign")
        ).add_to(markers_group)

    # 4. Định vị GPS TỰ ĐỘNG CẬP NHẬT
    LocateControl(
        auto_start=True,
        flyTo=True,
        keepCurrentZoomLevel=False,
        setView='untilPanOrZoom',
        locateOptions={
            'enableHighAccuracy': True,
            'watch': True,
            'maximumAge': 1000,
            'timeout': 10000
        },
        strings={"title": "Theo dõi vị trí thời gian thực"}
    ).add_to(m)

    # 5. Bản đồ thu nhỏ MiniMap
    mini_map = MiniMap(
        tile_layer=folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri'
        ),
        toggle_display=True,
        position='bottomright'
    )
    m.add_child(mini_map)

    # 6. Quản lý Lớp bản đồ
    folium.LayerControl(position='topright', collapsed=True).add_to(m)

    # --- 7. TÙY CHỈNH UI RESPONSIVE (PC / TABLET / MOBILE) ---
    gradient_ui_html = '''
    <script src="https://cdn.jsdelivr.net/npm/leaflet-rotate@0.2.8/dist/leaflet-rotate-src.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <!-- KHUNG TÌM KIẾM ĐỊA ĐIỂM -->
    <div id="search-bar-container">
        <i class="fa-solid fa-magnifying-glass search-icon"></i>
        <input type="text" id="global-search-input" placeholder="Tìm kiếm địa điểm..." autocomplete="off" oninput="debounceGlobalSearch()" />
        <button id="clear-search-btn" onclick="clearGlobalSearch()" style="display: none;">
            <i class="fa-solid fa-xmark"></i>
        </button>
        <div id="global-search-results" class="global-autocomplete-box"></div>
    </div>

    <!-- PANEL DẪN ĐƯỜNG -->
    <div id="routing-panel" class="panel-collapsed">
        <div class="panel-header" onclick="toggleRoutingPanel()">
            <i class="fa-solid fa-route"></i>
            <h3>Dẫn Đường</h3>
            <i class="fa-solid fa-chevron-up toggle-icon" id="panel-toggle-btn"></i>
        </div>
        
        <div class="panel-body">
            <div class="input-group">
                <i class="fa-solid fa-circle-dot icon-start"></i>
                <input type="text" id="start-input" placeholder="Nhập điểm đón (A)..." autocomplete="off" oninput="debounceSearch('start')" />
                <div id="start-results" class="autocomplete-box"></div>
            </div>

            <div class="input-group">
                <i class="fa-solid fa-location-dot icon-end"></i>
                <input type="text" id="end-input" placeholder="Nhập điểm đến (B)..." autocomplete="off" oninput="debounceSearch('end')" />
                <div id="end-results" class="autocomplete-box"></div>
            </div>

            <div class="button-group">
                <button id="route-btn" onclick="calculateRoute()">
                    <i class="fa-solid fa-paper-plane"></i> Tìm Đường
                </button>
                <button id="clear-btn" onclick="clearRoute()">
                    <i class="fa-solid fa-rotate-left"></i> Xóa
                </button>
            </div>

            <div id="route-info" class="info-card" style="display: none;"></div>
        </div>
    </div>

    <!-- KHUNG ĐỒNG HỒ GLASS DESIGN -->
    <div id="glass-clock-container">
        <div class="clock-icon">
            <i class="fa-regular fa-clock"></i>
        </div>
        <div class="clock-content">
            <div id="clock-time">00:00:00</div>
            <div id="clock-date">Thứ ..., --/--/----</div>
        </div>
    </div>

    <!-- NÚT RESET HƯỚNG BẢN ĐỒ VỀ BẮC -->
    <button id="reset-bearing-btn" title="Đặt lại hướng Bắc" onclick="resetMapBearing()">
        <i class="fa-solid fa-compass" id="compass-icon"></i>
    </button>

    <style>
        /* === CHUNG & TỐI ƯU CẢM ỨNG MOBILE === */
        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            -webkit-tap-highlight-color: transparent;
        }

        /* Nút Zoom & GPS Glassmorphism */
        .leaflet-bar,
        .leaflet-control-zoom,
        .leaflet-control-locate {
            border: none !important;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4) !important;
        }

        .leaflet-bar a,
        .leaflet-control-zoom-in,
        .leaflet-control-zoom-out,
        .leaflet-control-locate a {
            background: linear-gradient(135deg, rgba(30, 30, 47, 0.85) 0%, rgba(42, 42, 64, 0.85) 100%) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            color: #00d2ff !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
        }

        .leaflet-bar a:first-child {
            border-top-left-radius: 12px !important;
            border-top-right-radius: 12px !important;
        }

        .leaflet-bar a:last-child {
            border-bottom-left-radius: 12px !important;
            border-bottom-right-radius: 12px !important;
            border-top: none !important;
        }

        .leaflet-control-locate a {
            border-radius: 12px !important;
        }

        .leaflet-bar a:hover, .leaflet-control-locate a:hover {
            background: rgba(0, 210, 255, 0.25) !important;
            color: #ffffff !important;
            border-color: #00d2ff !important;
        }

        .leaflet-control-locate a span { color: #00d2ff !important; }

        /* Nút La Bàn */
        #reset-bearing-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(30, 30, 47, 0.85) 0%, rgba(42, 42, 64, 0.85) 100%);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #00d2ff;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }

        /* Đồng Hồ */
        #glass-clock-container {
            position: absolute;
            bottom: 25px;
            left: 345px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 18px;
            background: linear-gradient(135deg, rgba(30, 30, 47, 0.85) 0%, rgba(42, 42, 64, 0.85) 100%);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 18px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
            font-family: 'Segoe UI', Roboto, sans-serif;
            color: #ffffff;
        }

        .clock-icon {
            font-size: 22px;
            background: linear-gradient(45deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        #clock-time { font-size: 18px; font-weight: 700; color: #ffffff; }
        #clock-date { font-size: 11px; color: #a0a0b5; margin-top: 2px; }

        /* Khung Tìm Kiếm */
        #search-bar-container {
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            width: 420px;
            max-width: 90vw;
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, rgba(30, 30, 47, 0.85) 0%, rgba(42, 42, 64, 0.85) 100%);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 30px;
            padding: 6px 16px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }

        .search-icon { color: #00d2ff; font-size: 16px; margin-right: 10px; }

        #global-search-input {
            width: 100%;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 14px;
            padding: 8px 0;
        }

        #clear-search-btn { background: transparent; border: none; color: #a0a0b5; cursor: pointer; }

        .global-autocomplete-box {
            position: absolute;
            top: 100%;
            left: 0; right: 0;
            background: rgba(30, 30, 47, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            max-height: 250px;
            overflow-y: auto;
            z-index: 1050;
            margin-top: 8px;
            display: none;
        }

        /* Panel Dẫn Đường */
        #routing-panel {
            position: absolute;
            bottom: 25px;
            left: 20px;
            z-index: 1000;
            background: linear-gradient(135deg, rgba(30, 30, 47, 0.85) 0%, rgba(42, 42, 64, 0.85) 100%);
            padding: 16px;
            border-radius: 18px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
            font-family: 'Segoe UI', Roboto, sans-serif;
            width: 300px;
            color: #ffffff;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            transition: all 0.3s ease;
        }

        .panel-header {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }

        .panel-header i {
            font-size: 18px;
            background: linear-gradient(45deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .panel-header h3 { margin: 0; font-size: 15px; font-weight: 700; flex: 1; }
        .toggle-icon { display: none; color: #a0a0b5; font-size: 14px; }

        .panel-body { margin-top: 14px; }

        .input-group {
            position: relative;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }

        .input-group i { position: absolute; left: 12px; font-size: 14px; z-index: 2; }
        .icon-start { color: #00e676; }
        .icon-end { color: #ff5252; }

        .input-group input {
            width: 100%;
            padding: 9px 12px 9px 36px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            color: #ffffff;
            font-size: 13px;
            outline: none;
            box-sizing: border-box;
        }

        .autocomplete-box {
            position: absolute;
            bottom: 100%;
            left: 0; right: 0;
            background: rgba(37, 37, 56, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            max-height: 160px;
            overflow-y: auto;
            z-index: 1050;
            margin-bottom: 6px;
            display: none;
        }

        .autocomplete-item {
            padding: 10px 12px;
            font-size: 12px;
            color: #e0e0e0;
            cursor: pointer;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .button-group { display: flex; gap: 8px; margin-top: 12px; }

        .button-group button {
            flex: 1;
            padding: 9px;
            border: none;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        #route-btn { background: linear-gradient(135deg, #11998e, #38ef7d); color: #fff; }
        #clear-btn { background: linear-gradient(135deg, #ff416c, #ff4b2b); color: #fff; }

        .info-card {
            margin-top: 12px;
            padding: 10px;
            background: rgba(0, 210, 255, 0.15);
            border: 1px solid rgba(0, 210, 255, 0.3);
            border-radius: 10px;
            font-size: 12px;
            text-align: center;
            color: #ffffff;
        }

        /* === MEDIA QUERIES RESPONSIVE DÀNH CHO MOBILE (iOS/Android) === */
        @media (max-width: 768px) {
            /* 1. Thu nhỏ khung tìm kiếm chính */
            #search-bar-container {
                top: 12px;
                width: calc(100% - 80px);
                left: 15px;
                transform: none;
                padding: 4px 12px;
            }

            /* 2. Đưa nút La bàn sang kế bên ô tìm kiếm */
            #reset-bearing-btn {
                top: 12px;
                right: 12px;
                width: 38px;
                height: 38px;
                font-size: 16px;
            }

            /* 3. Ẩn đồng hồ để chừa không gian hiển thị bản đồ trên điện thoại */
            #glass-clock-container {
                display: none;
            }

            /* 4. Tối ưu Panel Dẫn Đường thành dạng Drawer vuốt dưới lên */
            #routing-panel {
                bottom: 12px;
                left: 12px;
                right: 12px;
                width: auto;
                padding: 12px 16px;
                border-radius: 16px;
            }

            .toggle-icon { display: block; }

            /* Trạng thái thu gọn trên mobile */
            #routing-panel.panel-collapsed .panel-body {
                display: none;
            }

            /* Di chuyển vị trí nút Zoom / GPS mặc định của Folium */
            .leaflet-top.leaflet-left {
                top: 65px !important;
            }

            .leaflet-control-layers {
                margin-top: 65px !important;
            }

            /* Tối ưu MiniMap nhỏ lại trên mobile */
            .leaflet-control-minimap {
                width: 80px !important;
                height: 80px !important;
            }
        }
    </style>

    <script>
        var mapObj = null;
        var startMarker = null;
        var endMarker = null;
        var searchMarker = null;
        var routePolyline = null;
        var searchTimer = null;
        var globalSearchTimer = null;

        /* CẬP NHẬT ĐỒNG HỒ */
        function updateRealTimeClock() {
            var now = new Date();
            var hours = String(now.getHours()).padStart(2, '0');
            var minutes = String(now.getMinutes()).padStart(2, '0');
            var seconds = String(now.getSeconds()).padStart(2, '0');
            document.getElementById('clock-time').innerText = `${hours}:${minutes}:${seconds}`;

            var days = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
            var dayName = days[now.getDay()];
            var date = String(now.getDate()).padStart(2, '0');
            var month = String(now.getMonth() + 1).padStart(2, '0');
            var year = now.getFullYear();
            document.getElementById('clock-date').innerText = `${dayName}, ${date}/${month}/${year}`;
        }

        /* ẨN / HIỆN PANEL DẪN ĐƯỜNG TRÊN MOBILE */
        function toggleRoutingPanel() {
            if (window.innerWidth <= 768) {
                var panel = document.getElementById('routing-panel');
                var icon = document.getElementById('panel-toggle-btn');
                if (panel.classList.contains('panel-collapsed')) {
                    panel.classList.remove('panel-collapsed');
                    icon.className = "fa-solid fa-chevron-down toggle-icon";
                } else {
                    panel.classList.add('panel-collapsed');
                    icon.className = "fa-solid fa-chevron-up toggle-icon";
                }
            }
        }

        /* XOAY BẢN ĐỒ */
        function enableMapRotation(map) {
            if (typeof map.setBearing === 'function' && typeof map.getBearing === 'function') {
                map.setBearing(0);
                map.on('rotate', function() {
                    var bearing = map.getBearing();
                    var compass = document.getElementById('compass-icon');
                    if (compass) {
                        compass.style.transform = `rotate(${-bearing}deg)`;
                    }
                });
            }
        }

        function resetMapBearing() {
            if (mapObj && typeof mapObj.setBearing === 'function') {
                mapObj.setBearing(0);
            }
        }

        function enableRightMouseDragRotation(map) {
            if (!map || typeof map.setBearing !== 'function' || typeof map.getBearing !== 'function') return;

            var container = map.getContainer();
            var rotationDrag = null;
            var suppressNextClick = false;
            var suppressContextMenu = false;

            container.addEventListener('mousedown', function(e) {
                if (e.button !== 2) return;
                e.preventDefault();
                e.stopPropagation();

                var wasDraggingEnabled = map.dragging && map.dragging.enabled();
                if (wasDraggingEnabled) map.dragging.disable();
                rotationDrag = {
                    startX: e.clientX,
                    startBearing: map.getBearing(),
                    wasDraggingEnabled: wasDraggingEnabled,
                    moved: false
                };
                suppressContextMenu = true;
                container.style.cursor = 'ew-resize';
            }, true);

            document.addEventListener('mousemove', function(e) {
                if (!rotationDrag) return;
                var deltaX = e.clientX - rotationDrag.startX;
                rotationDrag.moved = Math.abs(deltaX) > 3;
                map.setBearing(rotationDrag.startBearing + deltaX * 0.5);
            });

            document.addEventListener('mouseup', function(e) {
                if (!rotationDrag || e.button !== 2) return;
                suppressNextClick = rotationDrag.moved;
                if (rotationDrag.wasDraggingEnabled) map.dragging.enable();
                rotationDrag = null;
                container.style.cursor = '';
            });

            container.addEventListener('click', function(e) {
                if (!suppressNextClick) return;
                suppressNextClick = false;
                e.preventDefault();
                e.stopImmediatePropagation();
            }, true);

            container.addEventListener('contextmenu', function(e) {
                if (!suppressContextMenu) return;
                suppressContextMenu = false;
                e.preventDefault();
            }, true);
        }

        document.addEventListener("DOMContentLoaded", function() {
            updateRealTimeClock();
            setInterval(updateRealTimeClock, 1000);

            for (var key in window) {
                if (key.startsWith("map_") && window[key] instanceof L.Map) {
                    mapObj = window[key];
                    break;
                }
            }

            if (mapObj) {
                enableMapRotation(mapObj);
                enableRightMouseDragRotation(mapObj);
                mapObj.invalidateSize();

                mapObj.on('click', function(e) {
                    if (!startMarker) {
                        setStartPoint(e.latlng.lat, e.latlng.lng, "Điểm chọn trên bản đồ");
                    } else if (!endMarker) {
                        setEndPoint(e.latlng.lat, e.latlng.lng, "Điểm chọn trên bản đồ");
                        calculateRoute();
                    }
                });
            }

            document.addEventListener('click', function(e) {
                if (!e.target.closest('.input-group')) {
                    document.getElementById('start-results').style.display = 'none';
                    document.getElementById('end-results').style.display = 'none';
                }
                if (!e.target.closest('#search-bar-container')) {
                    document.getElementById('global-search-results').style.display = 'none';
                }
            });
        });

        /* TÌM KIẾM ĐỊA ĐIỂM CHÍNH */
        function debounceGlobalSearch() {
            clearTimeout(globalSearchTimer);
            var query = document.getElementById('global-search-input').value;
            var clearBtn = document.getElementById('clear-search-btn');

            if (query.length > 0) {
                clearBtn.style.display = 'block';
            } else {
                clearBtn.style.display = 'none';
                document.getElementById('global-search-results').style.display = 'none';
                return;
            }

            globalSearchTimer = setTimeout(() => {
                if (query.length < 2) return;
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=vn&limit=5`)
                    .then(res => res.json())
                    .then(data => {
                        var box = document.getElementById('global-search-results');
                        box.innerHTML = '';
                        if (data.length > 0) {
                            box.style.display = 'block';
                            data.forEach(item => {
                                var div = document.createElement('div');
                                div.className = 'autocomplete-item';
                                div.innerText = item.display_name;
                                div.onclick = function() {
                                    goToLocation(parseFloat(item.lat), parseFloat(item.lon), item.display_name);
                                    box.style.display = 'none';
                                };
                                box.appendChild(div);
                            });
                        } else {
                            box.style.display = 'none';
                        }
                    });
            }, 300);
        }

        function goToLocation(lat, lng, label) {
            if (searchMarker) mapObj.removeLayer(searchMarker);
            searchMarker = L.marker([lat, lng]).addTo(mapObj)
                .bindPopup("<b>Địa điểm tìm kiếm:</b><br>" + label).openPopup();
            mapObj.setView([lat, lng], 15, { animate: true });
        }

        function clearGlobalSearch() {
            document.getElementById('global-search-input').value = '';
            document.getElementById('clear-search-btn').style.display = 'none';
            document.getElementById('global-search-results').style.display = 'none';
            if (searchMarker) mapObj.removeLayer(searchMarker);
            searchMarker = null;
        }

        /* DẪN ĐƯỜNG */
        function debounceSearch(type) {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                var query = document.getElementById(type + '-input').value;
                if (query.length < 2) {
                    document.getElementById(type + '-results').style.display = 'none';
                    return;
                }
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=vn&limit=5`)
                    .then(res => res.json())
                    .then(data => {
                        var box = document.getElementById(type + '-results');
                        box.innerHTML = '';
                        if (data.length > 0) {
                            box.style.display = 'block';
                            data.forEach(item => {
                                var div = document.createElement('div');
                                div.className = 'autocomplete-item';
                                div.innerText = item.display_name;
                                div.onclick = function() {
                                    if (type === 'start') {
                                        setStartPoint(parseFloat(item.lat), parseFloat(item.lon), item.display_name);
                                    } else {
                                        setEndPoint(parseFloat(item.lat), parseFloat(item.lon), item.display_name);
                                    }
                                    box.style.display = 'none';
                                };
                                box.appendChild(div);
                            });
                        } else {
                            box.style.display = 'none';
                        }
                    });
            }, 300);
        }

        function setStartPoint(lat, lng, label) {
            if (startMarker) mapObj.removeLayer(startMarker);
            startMarker = L.marker([lat, lng], {title: "Điểm đón (A)"}).addTo(mapObj)
                .bindPopup("<b>Điểm đón (A)</b><br>" + label).openPopup();
            document.getElementById('start-input').value = label;
        }

        function setEndPoint(lat, lng, label) {
            if (endMarker) mapObj.removeLayer(endMarker);
            endMarker = L.marker([lat, lng], {title: "Điểm đến (B)"}).addTo(mapObj)
                .bindPopup("<b>Điểm đến (B)</b><br>" + label).openPopup();
            document.getElementById('end-input').value = label;
        }

        async function calculateRoute() {
            var infoCard = document.getElementById('route-info');
            
            if (!startMarker || !endMarker) {
                infoCard.style.display = 'block';
                infoCard.innerHTML = "<span style='color: #ff5252;'>Vui lòng chọn đủ Điểm đón & Điểm đến!</span>";
                return;
            }

            var latLngA = startMarker.getLatLng();
            var latLngB = endMarker.getLatLng();

            var osrmUrl = `https://router.project-osrm.org/route/v1/driving/${latLngA.lng},${latLngA.lat};${latLngB.lng},${latLngB.lat}?overview=full&geometries=geojson`;

            infoCard.style.display = 'block';
            infoCard.innerHTML = "<i class='fa-solid fa-spinner fa-spin'></i> Đang tính toán đường đi...";

            fetch(osrmUrl)
                .then(res => res.json())
                .then(data => {
                    if (data.routes && data.routes.length > 0) {
                        var route = data.routes[0];
                        var coords = route.geometry.coordinates.map(c => [c[1], c[0]]);

                        if (routePolyline) mapObj.removeLayer(routePolyline);

                        routePolyline = L.polyline(coords, {color: '#00d2ff', weight: 6, opacity: 0.9}).addTo(mapObj);
                        mapObj.fitBounds(routePolyline.getBounds(), {padding: [40, 40]});

                        var distKm = (route.distance / 1000).toFixed(2);
                        infoCard.innerHTML = `<i class="fa-solid fa-road"></i> Khoảng cách: <b>${distKm} km</b>`;
                    } else {
                        infoCard.innerHTML = "<span style='color: #ff5252;'>Không tìm thấy đường đi thích hợp!</span>";
                    }
                })
                .catch(err => {
                    infoCard.innerHTML = "<span style='color: #ff5252;'>Lỗi kết nối máy chủ dẫn đường!</span>";
                });
        }

        function clearRoute() {
            if (startMarker) mapObj.removeLayer(startMarker);
            if (endMarker) mapObj.removeLayer(endMarker);
            if (routePolyline) mapObj.removeLayer(routePolyline);
            startMarker = null;
            endMarker = null;
            routePolyline = null;
            document.getElementById('start-input').value = "";
            document.getElementById('end-input').value = "";
            document.getElementById('start-results').style.display = 'none';
            document.getElementById('end-results').style.display = 'none';
            var infoCard = document.getElementById('route-info');
            infoCard.style.display = 'none';
            infoCard.innerHTML = "";
        }
    </script>
    '''

    m.get_root().html.add_child(folium.Element(gradient_ui_html))

    # Lưu file index.html
    m.save(output_filename)
    print(f"[OK] Đã xuất file thành công: {output_filename}")
    webbrowser.open('file://' + os.path.realpath(output_filename))


if __name__ == "__main__":
    build_vietnam_routing_map()