/* ESP32 Dual Relay Web Server + HTTP API
   Relay 1 -> GPIO14
   Relay 2 -> GPIO27
   ACTIVE LOW RELAYS (LOW = ON)
   
   Compatible with cvzone Hand Gesture Control
*/

#include <WiFi.h>
#include <WebServer.h>

// WiFi credentials
const char* ssid = "Galaxy A15 5G";
const char* password = "1234567890";

// Relay pins
constexpr int RELAY1 = 14;
constexpr int RELAY2 = 27;

// Relay states
volatile bool r1 = false;
volatile bool r2 = false;

// Last control source
String lastSource = "None";
unsigned long lastCommandTime = 0;

// Web server on port 80
WebServer server(80);

// ===============================
// CORS Headers for Python requests
// ===============================
void sendCORSHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

// ===============================
// Relay Control
// ===============================
inline void setRelay(uint8_t relay, bool on, String source = "API") {
  if (relay == 1) {
    r1 = on;
    digitalWrite(RELAY1, on ? LOW : HIGH);
  } else if (relay == 2) {
    r2 = on;
    digitalWrite(RELAY2, on ? LOW : HIGH);
  }
  lastSource = source;
  lastCommandTime = millis();
  Serial.printf("[%s] Relay %d -> %s\n", source.c_str(), relay, on ? "ON" : "OFF");
}

bool validRelay(int r) {
  return r == 1 || r == 2;
}

// ===============================
// Web UI
// ===============================
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ESP32 Relay Control</title>
<style>
body { font-family: Arial; text-align:center; padding-top:20px; background:#1a1a2e; color:#fff; }
h2 { color:#16c79a; }
.b { font-size:28px; padding:18px; margin:12px; border-radius:12px; color:#fff; cursor:pointer; width:260px; display:inline-block; border:none; transition:0.3s; }
.on { background:#2ecc71; box-shadow:0 0 20px #2ecc71; }
.off { background:#e74c3c; }
.b:hover { transform:scale(1.05); }
.status { margin-top:20px; padding:15px; background:#252542; border-radius:10px; display:inline-block; }
.hand { color:#f9ed69; font-size:24px; }
.source { font-size:14px; color:#888; margin-top:10px; }
.connected { color:#2ecc71; }
.icon { font-size:40px; margin-bottom:10px; }
</style>
</head>
<body>
<h2>🤖 ESP32 Hand Gesture Relay Control</h2>
<p class="hand">✋ Use hand gestures or click buttons</p>

<div class="icon">💡</div>
<div id="r1" class="b off">Relay 1 OFF</div><br>
<div id="r2" class="b off">Relay 2 OFF</div>

<div class="status">
  <div>Last Control: <span id="source">-</span></div>
  <div class="source">1 finger=R1 ON | 2 fingers=R1 OFF | 3 fingers=R2 ON | 4 fingers=R2 OFF</div>
</div>

<script>
async function refresh() {
  try {
    const j = await (await fetch("/api/state")).json();
    upd("r1", j.r1);
    upd("r2", j.r2);
    document.getElementById("source").innerHTML = j.source || "Web";
  } catch(e) {}
}
function upd(id, val) {
  const e = document.getElementById(id);
  e.className = "b " + (val ? "on" : "off");
  e.innerHTML = "Relay " + id.charAt(1) + " " + (val ? "ON ✓" : "OFF");
}
document.getElementById("r1").onclick = () => fetch("/api/toggle?relay=1&source=Web").then(refresh);
document.getElementById("r2").onclick = () => fetch("/api/toggle?relay=2&source=Web").then(refresh);

refresh();
setInterval(refresh, 1000);
</script>
</body>
</html>
)rawliteral";

// ===============================
// API Handlers
// ===============================
void handleRoot() {
  server.send_P(200, "text/html", INDEX_HTML);
}

void handleApiToggle() {
  sendCORSHeaders();
  if (!server.hasArg("relay")) { server.send(400, "text/plain", "Missing relay"); return; }
  int r = server.arg("relay").toInt();
  if (!validRelay(r)) { server.send(400, "text/plain", "Invalid relay"); return; }
  String source = server.hasArg("source") ? server.arg("source") : "API";
  setRelay(r, (r == 1 ? !r1 : !r2), source);
  server.send(200, "application/json", "{\"ok\":1}");
}

void handleApiOn() {
  sendCORSHeaders();
  if (!server.hasArg("relay")) { server.send(400, "text/plain", "Missing relay"); return; }
  int r = server.arg("relay").toInt();
  if (!validRelay(r)) { server.send(400, "text/plain", "Invalid relay"); return; }
  String source = server.hasArg("source") ? server.arg("source") : "Hand Gesture";
  setRelay(r, true, source);
  server.send(200, "application/json", "{\"ok\":1}");
}

void handleApiOff() {
  sendCORSHeaders();
  if (!server.hasArg("relay")) { server.send(400, "text/plain", "Missing relay"); return; }
  int r = server.arg("relay").toInt();
  if (!validRelay(r)) { server.send(400, "text/plain", "Invalid relay"); return; }
  String source = server.hasArg("source") ? server.arg("source") : "Hand Gesture";
  setRelay(r, false, source);
  server.send(200, "application/json", "{\"ok\":1}");
}

void handleApiState() {
  sendCORSHeaders();
  char json[128];
  snprintf(json, sizeof(json), "{\"r1\":%d,\"r2\":%d,\"source\":\"%s\"}", 
           r1 ? 1 : 0, r2 ? 1 : 0, lastSource.c_str());
  server.send(200, "application/json", json);
}

void handleApiStatus() {
  sendCORSHeaders();
  if (!server.hasArg("relay")) { server.send(400, "text/plain", "Missing relay"); return; }
  int r = server.arg("relay").toInt();
  if (!validRelay(r)) { server.send(400, "text/plain", "Invalid relay"); return; }
  bool state = (r == 1 ? r1 : r2);
  char json[32];
  snprintf(json, sizeof(json), "{\"relay\":%d,\"state\":%d}", r, state ? 1 : 0);
  server.send(200, "application/json", json);
}

void handlePing() {
  sendCORSHeaders();
  server.send(200, "application/json", "{\"status\":\"ok\",\"device\":\"ESP32 Relay\"}");
}

// ===============================
// Setup
// ===============================
void setup() {
  Serial.begin(115200);

  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  setRelay(1, false);
  setRelay(2, false);

  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.println(WiFi.localIP());

  // API routes
  server.on("/", handleRoot);
  server.on("/api/toggle", handleApiToggle);
  server.on("/api/on", handleApiOn);
  server.on("/api/off", handleApiOff);
  server.on("/api/state", handleApiState);
  server.on("/api/status", handleApiStatus);
  server.on("/api/ping", handlePing);  // Health check endpoint

  server.begin();
  Serial.println("Server Ready!");
  Serial.println("Hand Gesture Control Enabled!");
}

// ===============================
// Loop
// ===============================
void loop() {
  server.handleClient();
}
