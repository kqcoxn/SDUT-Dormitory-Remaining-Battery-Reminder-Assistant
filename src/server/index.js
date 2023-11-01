//导入
const server = require("./server");
const apiRouter = require("./apiRouter");
const pageRouter = require("./pageRouter");
const postRouter = require("./postRouter");

//引入路由
server.use(apiRouter.route, pageRouter.route, postRouter.route);

//启动
server.start();
