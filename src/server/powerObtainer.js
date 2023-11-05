//低版本适配
if (!Array.prototype.at) {
  Array.prototype.at = function (pos) {
    var normalizedPos = Math.floor(pos);
    if (normalizedPos < 0) normalizedPos = this.length + normalizedPos;
    return this[normalizedPos];
  };
}

//导入
const https = require("https");
const fs = require("fs");
const querystring = require("querystring");
const cheerio = require("cheerio");
const tools = require("./tools");
const headers = require("./data/Headers.json");
const socketData = querystring.stringify(require("./data/Socket.json"));
const acData = querystring.stringify(require("./data/AC.json"));
var history = require("./data/History.json");
const settings = require("./data/Settings.json");

//请求
const options = {
  protocol: "https:",
  hostname: "hqfw.sdut.edu.cn",
  method: "POST",
  port: "443",
  path: "/stu_elc.aspx",
  headers: headers,
};

function getPower(powerType) {
  return new Promise((resolve, reject) => {
    let data = "";

    let req = https.request(options, (res) => {
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        resolve(filterData(data));
      });
    });

    req.write(powerType == "socket" ? socketData : acData);
    req.end();
  });
}

function filterData(data) {
  let $ = cheerio.load(data);
  let spanTag = $("#lblyue");
  let spanText = spanTag.text().match(/\d+\.\d+/)[0];
  return +spanText;
}

//储存
var nowPowerData = {
  socket: -1,
  ac: -1,
  todayConsumption: {
    socket: -1,
    ac: -1,
  },
  yesterdayConsumption: {
    socket: -1,
    ac: -1,
  },
};

history[tools.getNowtime("stdDate")] = [-1, -1, 0, 0];
function recordHistory(addedSocketCost = 0, addedACCost = 0) {
  nowTime = tools.getNowtime("stdDate");
  history[nowTime] = [
    nowPowerData.socket,
    nowPowerData.ac,
    history[nowTime][2] + addedSocketCost,
    history[nowTime][3] + addedACCost,
  ];
  fs.writeFile("./data/History.json", JSON.stringify(history), (err) => {
    if (err) {
      tools.logWithTime("保存历史失败", `(${err})`);
    } else {
      if (addedSocketCost + addedACCost > 0) {
        tools.logWithTime("已更新充值电量");
      }
      tools.logWithTime("已保存更新");
    }
  });
}

//定时获取
async function updatePowerData() {
  //获取数据
  nowPowerData.socket = await getPower("socket");
  nowPowerData.ac = await getPower("ac");

  //保存
  recordHistory();

  //更新差值
  nowTime = tools.getNowtime("stdDate");
  last1DayTime = tools.getNowtime("stdDate", -1);
  nowPowerData.todayConsumption.socket = tools.fixFloat(
    history[last1DayTime][0] - nowPowerData.socket + history[nowTime][2] / 0.55,
    2
  );
  nowPowerData.todayConsumption.ac = tools.fixFloat(
    history[last1DayTime][1] - nowPowerData.ac + history[nowTime][3] / 0.55,
    2
  );
  last2DayTime = tools.getNowtime("stdDate", -2);
  nowPowerData.yesterdayConsumption.socket = tools.fixFloat(
    history[last2DayTime][0] -
      history[last1DayTime][0] +
      history[nowTime][2] / 0.55,
    2
  );
  nowPowerData.yesterdayConsumption.ac = tools.fixFloat(
    history[last2DayTime][1] -
      history[last1DayTime][1] +
      history[nowTime][3] / 0.55,
    2
  );

  //提示
  tools.logWithTime("已更新数据:");
  console.log(
    ` - 剩余照明电量: ${nowPowerData.socket} kW·h (${(
      nowPowerData.socket * 0.55
    ).toFixed(2)}￥)`
  );
  console.log(
    ` - 剩余空调电量: ${nowPowerData.ac} kW·h (${(
      nowPowerData.ac * 0.55
    ).toFixed(2)}￥)`
  );
  console.log(
    ` - 今日照明耗电: ${nowPowerData.todayConsumption.socket} kW·h (${(
      nowPowerData.todayConsumption.socket * 0.55
    ).toFixed(2)}￥)`
  );
  console.log(
    ` - 今日空调耗电: ${nowPowerData.todayConsumption.ac} kW·h (${(
      nowPowerData.todayConsumption.ac * 0.55
    ).toFixed(2)}￥)`
  );
}

const queryIntervalHour = settings.queryIntervalHour;
const startTime = settings.startTime;
const endTime = settings.endTime;
setInterval(() => {
  let nowHour = new Date().getHours();
  if (nowHour >= startTime && nowHour < endTime) {
    updatePowerData();
  }
}, Math.round(queryIntervalHour * 60 * 60 * 1000));

//导出
module.exports = {
  powerData: nowPowerData,
  updatePowerData,
  recordHistory,
};
