//导入
const http = require("http");
const fs = require("fs");
const zlib = require("zlib");
const { URL } = require("url");
const powerObtainer = require("./powerObtainer");
const tools = require("./tools");
const settings = require("./data/Settings.json");

//参数
const adress = "http://localhost";
const port = settings.port;
const router = {
  "/404": (res) => {
    res.writeHead(404, {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Encoding": "gzip",
    });
    let gzip = zlib.createGzip();
    gzip.pipe(res);
    gzip.end(fs.readFileSync("./static/404.html"));
  },
};

//合并路径
function use(...objList) {
  objList.forEach((obj) => {
    Object.assign(router, obj);
  });
}

//启用
function start() {
  http
    .createServer((req, res) => {
      let url = new URL(req.url, adress);
      let searchParams = url.searchParams;
      let isPost = req.method == "POST";
      tools.logWithTime(
        `'${req.method}' with "${url.pathname}" from "Port:${req.socket.remotePort}"`
      );
      try {
        if (isPost) {
          router[url.pathname](searchParams);
          res.end("{'status'='done'}");
        } else {
          router[url.pathname](res);
        }
        tools.logWithTime("(success)");
      } catch (error) {
        router["/404"](res);
        if (settings.isLogError) {
          tools.logWithTime("(fail, error:", error, ")");
        } else {
          tools.logWithTime("(fail)");
        }
      }
    })
    .listen(port, () => {
      tools.logWithTime("server started on", adress + ":" + port);
      powerObtainer.updatePowerData();
    });
}

//导出
module.exports = {
  start,
  use,
};
