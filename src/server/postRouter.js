//导入
const powerObtainer = require("./powerObtainer");

//路由
const route = {
  "/update/powerHistory": (searchParams) => {
    powerObtainer.recordHistory(
      +searchParams.get("addedSocketCost"),
      +searchParams.get("addedACCost")
    );
  },
};

//导出
module.exports = {
  route,
};
