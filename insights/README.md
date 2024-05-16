如果你还需要监控新闻站点，可以在这里启动work_process进程

首次使用前请先在pb admin界面中配置roleplays表单，在这里可以配置llm的身份信息和关注点，这将影响信息发掘和整理的效果，同时也影响report的生成风格。

roleplays可以配置多个，但每次只会选择更改时间最新且activated为true的。

**roleplay 字段说明：**

- character 以什么身份挖掘线索（这决定了llm的关注点和立场）
- focus 关注什么方面的线索
- focus_type 线索类型
- good_samples1 你希望llm给出的线索描述模式（给两个sample）
- good_samples2 你希望llm给出的线索描述模式（给两个sample）
- bad_samples 规避的线索描述模式
- report_type 报告类型

填好之后保证activated为true。

之后打开 **sites表单**

通过这个表单可以指定自定义信源，系统会启动后台定时任务，在本地执行信源扫描、解析和分析。

sites 字段说明：

- url, 信源的url，信源无需给定具体文章页面，给文章列表页面即可，wiseflow client中包含两个通用页面解析器，90%以上的新闻类静态网页都可以很好的获取和解析。
- per_hours, 扫描频率，单位为小时，类型为整数（1~24范围，我们建议扫描频次不要超过一天一次，即设定为24）
- activated, 是否激活。如果关闭则会忽略该信源，关闭后可再次开启。开启和关闭无需重启docker容器，会在下一次定时任务时更新。

wiseflow client自定义信源的扫描调度策略是：每小时启动一次，会先看是否有满足频率要求的指定信源，如果没有的话，会看是否集成了专有爬虫，如果有的话，每24小时会运行一遍专有爬虫。

注意：如果使用sites指定信源，专有爬虫也需要配置在这里。

最后回到上级目录，重新启动 run.sh

注意： 适配特定网站的专有爬虫配置请参考 /scrapers/README.md

更多信息请参考：https://github.com/TeamWiseFlow/wiseflow/tree/master/client
