'use strict';
/** Chạy server: node src/server.js  (mặc định http://127.0.0.1:3000) */
const { createApp } = require('./app');

const port = Number(process.env.PORT || 3000);
const host = process.env.HOST || '127.0.0.1';
const { server, features } = createApp();

server.listen(port, host, () => {
  console.log(`CRM Lead & Marketing (Node.js) chạy tại http://${host}:${port}`);
  console.log('Các feature đã nạp:', features.map((f) => f.key).join(', ') || '(không có)');
});
