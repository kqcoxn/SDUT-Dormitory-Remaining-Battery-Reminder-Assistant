//导入
const zlib = require("zlib");
const powerObtainer = require("./powerObtainer");

//传输器
function sender(res, str) {
  res.writeHead(200, {
    "Content-Type": `text/plain; charset=utf-8`,
    "Content-Encoding": "gzip",
  });
  let gzip = zlib.createGzip();
  gzip.pipe(res);
  gzip.end(str.toString());
}

//路由
const route = {
  "/api/socket": (res) => {
    sender(res, powerObtainer.powerData.socket);
  },
  "/api/ac": (res) => {
    sender(res, powerObtainer.powerData.ac);
  },
  "/api/today/socket": (res) => {
    sender(res, powerObtainer.powerData.todayConsumption.socket);
  },
  "/api/today/ac": (res) => {
    sender(res, powerObtainer.powerData.todayConsumption.ac);
  },
  "/api/yesterday/socket": (res) => {
    sender(res, powerObtainer.powerData.yesterdayConsumption.socket);
  },
  "/api/yesterday/ac": (res) => {
    sender(res, powerObtainer.powerData.yesterdayConsumption.ac);
  },
};

//导出
module.exports = {
  route,
};
