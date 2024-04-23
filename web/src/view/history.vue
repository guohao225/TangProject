<template>
  <div id="history-box">
    <el-icon :size="20" class="refresh" @click="refresh">
      <Refresh/>
    </el-icon>
    <div id='history-view' class="history-view"></div>
  </div>
</template>

<script>
import {Refresh} from "@element-plus/icons-vue";
import {drawHistoryCircle2} from "@/view/drawHistoryItem";
import * as d3 from "d3";
import d3Tip from "d3-tip";

export default {
  name: "history",
  data() {
    return {
      mode: 'sample',
      modes: ['sample', 'entity'],

      history: [
        {'name': 'sample1', operation: ['delete', 'change'], id: 0},
        {'name': 'sample2', operation: ['delete', 'change', 'add'], id: 1},
        {'name': 'sample3', operation: ['change'], id: 2},
        {'name': 'sample4', operation: ['change', 'add'], id: 3}
      ],
      curHistoryName: ''
    }
  },
  components: {
    Refresh
  },
  mounted() {
    this.init()
  },
  watch: {
    '$store.state.operationRecord'(newV) {
      this.init(newV)
    },
    '$store.state.findOperation'(newV){
      this.findOperationsLocation(newV)
      console.log(newV)
    }
  },
  methods: {
    init(data) {
      console.log(data)
      let domID = `history-view`
      let baseDom = document.getElementById(domID)
      //清空画布
      baseDom.innerHTML = ""
      let width = baseDom.clientWidth
      let height = baseDom.clientHeight
      let margin = 50
      let long = 100

      let svg = this.$d3.select(`#history-view`)
        .append('svg')
        .attr('width', 30000)
        .attr('height', height)
        .attr('class', 'history-view-svg')
      // 创建缩放行为
      var zoom = d3.zoom()
        .on("zoom", zoomed);
      // 绑定缩放行为到SVG元素上
      svg.call(zoom);
      // 创建拖拽行为
      var drag = d3.drag()
        .on("drag", dragged);
      // 绑定拖拽行为到SVG元素上
      svg.call(drag);
      // 缩放行为的回调函数
      function zoomed(event) {
        // 获取当前缩放的比例和平移的距离
        var transform = event.transform;
        // 更新SVG视图的位置和大小
        svg.attr("transform", transform);
      }
      // 拖拽行为的回调函数
      function dragged(event, d) {
        // 获取当前缩放的比例和平移的距离
        var transform = d3.zoomTransform(this);
        // 计算拖拽的距离并更新SVG视图的位置
        svg.attr("transform", transform.translate(event.dx, event.dy));
      }

      //绘制一个操作流程g元素：line+circle
      let oper = svg.selectAll('.opterStep')
        .data(data)
        .enter()
        .append('g')
        .attr('transform', (d, i) => {
          return `translate(${i * long + (margin + 30) + i * 8}, ${height / 2})`
        })
      .attr('class','operationStep')

      //绘制流程：自定义节点+连接线段
      oper.append(drawHistoryCircle2)
        .on('click', async (e, d) => {
          const tooltip = d3Tip()
            .attr('class', 'tips')
            .html(d=>{
              return `<div
            style="width: auto;
            height: 20px;
            border-radius: 4px;
            background: #ffffff;
            padding: 10px;
            box-shadow: 2px 2px 1px 1px #f6f7f8;
            position: relative;
            pointer-events: none;
            ">
            <div style="width: 0;height: 0;
            border-style: solid;
            position: absolute;
            left: 45%;
            bottom: -10px;
            border-width: 0px 10px 10px 10px;
            border-color: transparent transparent #46484a transparent;
            transform:rotate(180deg)
            "></div>
            name:${d.name}</div>`
            })
          let target = this.$d3.select(e.target)
          //判断是哪种节点
          let nodeClass = target.attr('class')
          let data = []
          if(nodeClass == 'bar'){
            let sampleData = target.datum()
            data = await this.$dataMan.getSampleOperationRecords(sampleData.id, parseInt(d.name.substr(d.name.length-1,1)))
            data = data.data.res
          }else if(nodeClass == 'arc'){
            data = await this.$dataMan.getLoopOperationRecords(parseInt(d.name.substr(d.name.length-1,1)))
            data = data.data.res
          }
          else {
            return
          }
          console.log(data)
          let frame = this.$d3.select(target.node().parentNode)
          frame.call(tooltip)
          // let box = frame.node().bbox()
          frame.selectAll('.opers').remove()
          let xOffset = 30
          let yOffset = 20
          let step = 30
          let lineGenerator = d3.line()
            .x(function (d) {
              return d.x;
            })
            .y(function (d) {
              return d.y;
            });
          let operStep = frame.selectAll('.opers')
            .data(data)
            .enter()
            .append('g')
            .attr('transform', (d, i) => {
              return `translate(${xOffset}, ${(i + 1) * yOffset})`
            })
            .attr('class', 'opers')
          let innerStep = operStep.selectAll('.oneStep')
            .data(d => {
              let data = []
              d.data.forEach((item, i)=>{
                data.push({name:item, size:d.data.length, msg:d.msg[i], type:d.type})
              })
              return data
            })
            .enter()
            .append('g')
            .attr('transform', (d, i) => {
              `translate(${i * step}, 0)`
            })
          innerStep.append('circle')
            .attr('r', 6)
            .attr('cx', (d, i) => i * step)
            .attr('cy', 0)
            .attr('fill', (d, i)=>{
              // eslint-disable-next-line no-constant-condition
              let index = (d.type==0||d.type==1)?2:1
              let msg = JSON.parse(d.msg[index])
              return this.$dataMan.COLORS[msg[0]]
            })
          .on('mouseover', (e, d)=>tooltip.show(d, e.target))
          .on('mouseout', (d)=>tooltip.destroy())
          innerStep.append('path')
            .datum((d, i) => {
              if(i == d.size-1)return []
              return [{x: i * step + 6, y: 0, type:d.type}, {x: (i + 1) * step - 3, y: 0, type:d.type}]
            })
            .attr("d", lineGenerator)
            .attr("stroke", "#63ade5")
            .attr("stroke-dasharray", d=>{
              data = d[0]
              if(data)
              switch (data.type){
                case 0:return "0, 0"
                case 1:return "5, 5"
                case 2:return "1, 1"
              }
            })
            .attr("stroke-width", 2)
            .attr("fill", "#63ade5")

          operStep.append('path')
            .datum((d, i) => {
              return [{x: -xOffset, y: -yOffset * (i + 1), type:d.type}, {x: 0, y: 0, type:d.type}]
            })
            .attr("d", lineGenerator)
            .attr("stroke-dasharray", d=>{
                switch (d[0].type){
                  case 0:return "0, 0"
                  case 1:return "5, 5"
                  case 2:return "1, 1"
                }
            })
            .attr("stroke", "#63ade5")
            .attr("stroke-width", 2)
            .attr("fill", "none")

          // //重新布局
          this.updateLayout()
        })
        .on('contextmenu', (e, d)=>{
          //获取该轮已标注的样本
          e.preventDefault()
          let loopID = d.name.charAt(d.name.length-1)
          this.$dataMan.reLabel(loopID).then(res=>{
            //获取样本
            this.$dataMan.getSelected().then(res=>{
              this.$store.commit('setMainData', res.data.res)
              this.$store.commit('setDataList', res.data.list)
            })
          })
        })
      oper.append('circle').attr('r', 4)
        .attr('data-status', 'close')
        .attr('fill', '#f1f1f1')
        .on('click', (e, d)=>{
          let frame = this.$d3.select(e.target.parentNode)
          frame.selectAll('.opers').remove()
        })
      //添加连接线段
      oper.append('line')
        .datum((d, i)=>{
          if (i == data.length - 1) return {}
          return {x1: 20, y1: 0, x2: long - 10, y2: 0}
        })
        .attr('x1', d=>d.x1)
        .attr('y1', d=>d.y1)
        .attr('x2', d=>d.x2)
        .attr('y2', d=>d.y2)
        .attr('stroke', 'black')
        .attr('class', 'operationLine')

      //添加提示信息
      let tips = svg.append('g')
        .attr('transform',  `translate(50, ${height-20})`)
    },
    refresh() {
      let dom = document.getElementById('history-view')
      dom.innerHTML = ''
      if (this.$store.state.operationRecord.length === 0) {
        this.$dataMan.getOperationRecords().then(res => {
          console.log(res.data.res)
          this.init(res.data.res)
        })
      } else {
        this.init(this.$store.state.operationRecord)
      }
    },
    findOperationsLocation(data){
      let loopId = data.loop
      let operEle = this.$d3.select(`#loop${loopId}`).node()
      if(operEle == null)return
      let box = operEle.getBBox()
      this.$d3.select(`#loop${loopId}`)
        .append('circle')
        .attr('r', box.width/2+2)
        .attr('cx', box.x+box.width/2)
        .attr('cy', box.y+box.height/2)
        .attr('fill', 'none')
        .attr('stroke', 'red')
        .attr('stroke-width', 3)
        .attr('class', 'highLight')

      this.$d3.select('.history-view-svg').on('mouseup', (e)=>{
        this.$d3.select('.highLight').remove()
      })
    },
    updateLayout(){
      let operationStep = this.$d3.selectAll('.operationStep')
      let nodes = operationStep.nodes()
      let rect = document.querySelector('#history-view')
      let span = 50
      let y = rect.clientHeight/2
      let that = this
      operationStep.attr('transform', function (d, i){
        let x = span
        let translate = `translate(${x}, ${y})`
        let curNode = that.$d3.select(this)
        let box = curNode.node().getBBox()
        let line = curNode.select('line').attr('x2', function (d, i){
          let xb = that.$d3.select(this).attr('x1')
          if(xb)
          return 20+box.width-30
        })
        span+=box.width
        return translate
      })
    },
  }
}
</script>

<style scoped>
#history-box {
  position: relative;
  width: 99%;
  min-height: 100px;
  height: 30vh;
  overflow: auto;
}

.history_mode {
  position: absolute;
  width: 60px;
  height: 25px;
  right: 10px;
  top: 10px;
}

.history-view {
  height: 160px;
  width: 99%;
  background-color: #ffffff;
  /*background-color: #f1f1f1;*/
}

.refresh {
  position: absolute;
  right: 20px;
  top: 10px;
}
</style>