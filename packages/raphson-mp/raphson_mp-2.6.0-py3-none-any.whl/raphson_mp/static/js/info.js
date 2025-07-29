const proto = window.location.protocol;
const port = window.location.port != "" ? window.location.port : (proto == "https:" ? 443 : 80);
document.getElementById("dav-nautilus").textContent = proto.replace("http", "dav") + "//" + window.location.host + "/dav";
document.getElementById("dav-dolphin").textContent = proto.replace("http", "webdav") + "//" + window.location.host + "/dav";
document.getElementById("material-host").textContent = window.location.hostname;
document.getElementById("material-port").textContent = port;
document.getElementById("material-proto").textContent = proto.substring(0, proto.length - 1).toUpperCase();
document.getElementById("davx5-url").textContent = proto + "//" + window.location.hostname + "/dav";
document.getElementById("dav-windows").textContent = "net use R: \\\\" + window.location.hostname + (proto == "https:" ? "@SSL" : "") + "@" + port + "\\dav\\ /savecred";
