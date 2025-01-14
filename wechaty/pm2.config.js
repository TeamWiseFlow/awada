// 名称任意，按照个人习惯来
module.exports = {
    apps: [
      {
        name: 'wechaty', // 应用名称
        script: './src/index.js', // 启动文件地址
        cwd: './', // 当前工作路径
        watch: false,
        ignore_watch: [
          // 忽视这些目录的变化
          'node_modules',
          'logs',
          'public',
          'config',
          'database/*'
        ],
        node_args: '--harmony', // node的启动模式
        env: {
          NODE_ENV: 'development', // 设置运行环境，此时process.env.NODE_ENV的值就是development
          ORIGIN_ADDR: 'http://www.yoduao.com'
        },
        env_production: {
          NODE_ENV: 'production',
        },
        out_file: './logs/out.log', // 普通日志路径
        error_file: './logs/err.log', // 错误日志路径
        merge_logs: true,
        log_date_format: 'YYYY-MM-DD HH:mm Z',
      },
    ],
  };