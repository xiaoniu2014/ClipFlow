


clips下面
source_dir 素材来源目录 
min_duration 最短素材时长，也就是低于这个时长的素材被舍去
max_duration 最长素材时长，多余这个时长的素材要被随机截取
start  该片段在整个拼接视频中的开始位置
end 该片段在整个拼接视频中的结束位置


output 中
duration  输出文件的总时长


我想要的结果是：
clips下有3个对象，这3个对象组成3个视频片段名字叫做A、B、C，A片段主要是从A对象下面的source_dir文件夹中随机挑选视频拼接的，挑选的视频最短不得小于min_duration，最长不得超过max_duration；A片短的总时长是start-end.B片段和C片段的组成也是同理，最后A、B、C3个片段拼接起来，总成结果视频