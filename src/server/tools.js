//导入
const { fchmod } = require("fs");
const zlib = require("zlib");

//时间模板
function getNowtime(format, gap = 0) {
  let now = new Date();
  now.setDate(now.getDate() + gap);

  let year = now.getFullYear();
  let month = String(now.getMonth() + 1).padStart(2, "0");
  let day = String(now.getDate()).padStart(2, "0");
  let hours = String(now.getHours()).padStart(2, "0");
  let minutes = String(now.getMinutes()).padStart(2, "0");
  let seconds = String(now.getSeconds()).padStart(2, "0");

  switch (format) {
    case "stdDateTime":
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    case "stdDate":
      return `${year}-${month}-${day}`;
    case "sdtTime":
      return `${hours}:${minutes}:${seconds}`;
    default:
      return now;
  }
}

//带时间输出
function logWithTime(...params) {
  console.log(`[${getNowtime("stdDateTime")}]`, ...params);
}

//解码gzip
function decodeGzipStr(str) {
  zlib.gunzip(Buffer.from(str, "base64"), (err, uncompressedStr) => {
    if (!err) {
      let result = uncompressedStr.toString("utf-8");
      logWithTime("已解压:", result);
      return result;
    } else {
      console.error("解压失败", `(${err})`);
    }
  });
}

//返回x位小数
function fixFloat(num, accu) {
  accu = 10 ** accu;
  return Math.round(num * accu) / accu;
}

//导出
module.exports = {
  logWithTime,
  decodeGzipStr,
  getNowtime,
  fixFloat,
};
