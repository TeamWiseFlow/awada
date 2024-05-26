import jieba

target = '【公众号 汇聚漕河泾】 绿地集团在徐汇绿地缤纷城举办“五五购物节国别好物进徐汇”活动，提供一站式的吃、喝、游、购新体验，并增设了俄罗斯套娃手工艺制作、国别文化教育小课堂等互动体验环节。'
compared = '【公众号 徐汇龙华发布】 在徐汇绿地缤纷城举办的“绿地集团五五购物节国别好物进徐汇”活动中，设置了国别文化教育小课堂和丝路音乐会，为家庭亲子和文化爱好者提供了寓教于乐的空间。'

target_tokens = set(jieba.lcut(target))
tokens = set(jieba.lcut(compared))

print(len(target_tokens & tokens) / min(len(target_tokens), len(tokens)))
