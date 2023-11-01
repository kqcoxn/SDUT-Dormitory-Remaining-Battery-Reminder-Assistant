//导入
const fs = require("fs");
const zlib = require("zlib");

//获取器
function getPage() {}

//传输器
function render(res, path, type = "text/html") {
  res.writeHead(200, {
    "Content-Type": `${type}; charset=utf-8`,
    "Content-Encoding": "gzip",
  });
  let gzip = zlib.createGzip();
  gzip.pipe(res);
  gzip.end(fs.readFileSync(path));
}

//路由
const route = {
  "/": (res) => {
    render(res, "./static/index.html");
  },
  "/favicon.ico": (res) => {
    render(res, "./static/favicon.ico", "image/x-icon");
  },
};

//导出
module.exports = {
  route,
};
