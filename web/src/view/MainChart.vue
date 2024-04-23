<template>
<!--  tabindex="0"-->
  <div class="chart-box"  @contextmenu="tagNext">
    <div class="chart-head"></div>
    <div class="time-view">
      {{timeSpan}}
    </div>
<!--    <div class="select-box">-->
<!--      <div>-->
<!--        <span>样本：</span><input v-model="sampleID" type="number" />-->
<!--      </div>-->
<!--      <div>-->
<!--        <span>轮次：</span><input v-model="loop" type="number" />-->
<!--      </div>-->
<!--      <div>-->
<!--        <button @click="selectLS">确认</button>-->
<!--&lt;!&ndash;        <svg&ndash;&gt;-->
<!--&lt;!&ndash;          @click="selectAction"&ndash;&gt;-->
<!--&lt;!&ndash;          t="1709193375778"&ndash;&gt;-->
<!--&lt;!&ndash;          class="select-icon"&ndash;&gt;-->
<!--&lt;!&ndash;          viewBox="0 0 1024 1024"&ndash;&gt;-->
<!--&lt;!&ndash;          version="1.1"&ndash;&gt;-->
<!--&lt;!&ndash;          xmlns="http://www.w3.org/2000/svg"&ndash;&gt;-->
<!--&lt;!&ndash;          p-id="5002"&ndash;&gt;-->
<!--&lt;!&ndash;          width="20"&ndash;&gt;-->
<!--&lt;!&ndash;          height="20"><path d="M107.29472 201.23648h783.36a30.72 30.72 0 0 0 0-61.44h-783.36a30.72 30.72 0 0 0 0 61.44zM507.41248 362.0352H106.5728c-13.73696 0-24.87296 13.75744-24.87296 30.72s11.136 30.72 24.87296 30.72h400.83968c13.73696 0 24.87296-13.75744 24.87296-30.72s-11.136-30.72-24.87296-30.72zM507.41248 594.51392H106.5728c-13.73696 0-24.87296 13.75744-24.87296 30.72s11.136 30.72 24.87296 30.72h400.83968c13.73696 0 24.87296-13.75744 24.87296-30.72s-11.136-30.72-24.87296-30.72zM895.77472 816.74752h-783.36a30.72 30.72 0 0 0 0 61.44h783.36a30.72 30.72 0 0 0 0-61.44zM889.71264 371.29216c16.1024-9.29792 36.22912 2.32448 36.22912 20.9152v228.63872c0 18.59072-20.12672 30.21312-36.22912 20.9152l-184.70912-106.63936c-16.1024-9.29792-16.1024-32.5376 0-41.83552l184.70912-121.99424z" fill="#333333" p-id="5003"></path></svg>&ndash;&gt;-->
<!--      </div>-->
<!--    </div>-->
    <div class="sample-view" id="sample-view"></div>
    <div class="sample-list-box">
      <div class="sample-list">
<!--        <div id="sample-list-chart"></div>-->
        <div class="sample-list-item"
             v-for="item in barData" :key="item"
             :style="{background:item.status>0?this.$dataMan.COLORS.labeled:'#909399'}"
             @mouseover="selectSampleData(item.id)"
             @click="tagSmp(item)"
        >{{item.title}}</div>
      </div>
      <div class="submit">
        <el-button type="primary" :style="{width:'90%', background:$dataMan.COLORS.buttons, border:'none'}" @click="nextTagLoop">下一轮</el-button>
        <el-icon v-if="showList" @click="showList=false" :size="20">
          <CaretBottom/>
        </el-icon>
        <el-icon v-else @click="sampleListShow" :size="20">
          <CaretTop/>
        </el-icon>
      </div>
    </div>
    <el-dialog v-model="showQuery"></el-dialog>
  </div>
</template>

<script>
import {CaretBottom, CaretTop} from "@element-plus/icons-vue";
import * as d3 from "d3";
import vData from "@/assets/data.json"
import { h } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: "MainChart",
  data() {
    return {
      margin_top: 50,
      size: 0,
      probability: 0,
      score: 0,

      showList: true,
      suggestID: -1,
      showQuery:false,
      beginTime:0,
      endTime:0,
      timeSpan:0,
      timer:null,
      barData:[],
      selector:false,
      loop:0,
      sampleID:0,
      tagedIndexs:[],
    }
  },
  components: {
    CaretBottom,
    CaretTop
  },
  mounted() {
    this.drawHead()
    this.beginTime = new Date()
    this.timer = setInterval(()=>{
      this.timeSpan = this.$dataMan.timefig(new Date(), this.beginTime)
    }, 1000)
    // this.drawVolcanoContoursChart()
  },
  computed:{
    strategy:function (){
      let data = this.$store.state.strategy
      // eslint-disable-next-line vue/no-side-effects-in-computed-properties
      data !== 'MNLP'?(this.score = 100):(this.score = 1)
      return data
    }
  },
  methods: {
    async drawChart(data) {
      let that = this
      let response = await this.$dataMan.suggestSample()
      this.suggestID = response.data.res
      let max = this.$d3.max(data, function (d) {
        let soc = that.strategy != 'MNLP'?d.LC:d.MNLP
        return soc
      })
      let sizeMax = this.$d3.max(data, function (d) {return d.size})
      let dom = document.getElementById('sample-view')
      dom.innerHTML = ""
      // this.drawVolcanoContoursChart()
      let width = dom.clientWidth
      let height = dom.clientHeight
      // 创建 SVG 元素
      const svg = this.$d3.select("#sample-view")
        .append("svg")
        .attr("width", 2000)
        .attr("height", 2000)
        .attr("class", "sample-view")
        .attr("style", "max-width: 100%; height: auto;")
        .on("click",(e)=>{
          let ele = e.target.nodeName
          if(ele === "svg"){
            let nodes = this.$d3.selectAll('.sample-node')
            nodes.attr('opacity', 1)
          }
        })
      .on('keydown',(e)=>{
        console.log(e)
      })
        // .attr("transform", `translate(${-(2000-width/2)}, ${-(2000-height/2)})`)

      //绘制散点图
      function zoomed(event) {
        // 获取当前缩放的比例和平移的距离
        var transform = event.transform;
        // 更新SVG视图的位置和大小
        svg.transition() //方式拖动时svg发生抖动
          .duration(50) // Adjust the duration as needed
          .attr("transform", transform);
      }
      var zoom = d3.zoom()
        .on("zoom", zoomed);
      svg.call(zoom);

      let yScale = this.$d3.scaleLinear().domain([0, 1]).range([height-300, 300])
      let xScale = this.$d3.scaleLinear().domain([0, max]).range([width, 0])
      let sizeScale = this.$d3.scaleLinear().domain([0, sizeMax]).range([15, 30])
      // 创建力导向模拟器
      const simulation = this.$d3.forceSimulation(data)
        .force("charge", this.$d3.forceManyBody().strength(-50))
        .force("link", this.$d3.forceLink().id(d => d.name))
        .force("center", this.$d3.forceCenter(width / 2, height / 2))
        .force("y", this.$d3.forceY(d => {
          // 根据概率值调整气泡位置
          let y = yScale(d.score)
          return y
        }))
        .force('x', this.$d3.forceX(d => {
          let off_pos = Math.random() > 0.5 ? 1 : -1
          let x = xScale(that.strategy!='MNLP'?d.LC:d.MNLP)
          return width / 2 - x * off_pos
        }))
      //绘制自定义节点
      const node = svg.selectAll('node')
        .data(data)
        .enter()
        .append('g')
        .attr("transform", d => `translate(${d.x},${d.y})`)
        .call(this.$d3.drag()
          .on('start', start)
          .on('drag', drag)
          .on('end', end)
        )
        .attr("class", 'sample-node')
        .on('click', async function (d) {
          let target = that.$d3.select(d.target)
          let tClass = target.attr('class')
          let data = that.$d3.select(d.target.parentNode).data()[0]
          if(tClass){
            switch (tClass) {
              case 'remove':await that.$dataMan.tagUpdateMany({name:data.data.name, type:data.data.type, oper:0});break;
              case 'change':await that.$dataMan.tagUpdateMany({name:data.data.name, type:data.data.type, oper:1});break;
              case 'search':that.showQuery=true;return;
            }
            let res = await that.$dataMan.getSelected()
            let base = res.data.res
            let lineData = res.data.list
            let loop = res.data.loop
            window.sessionStorage.setItem('loop', loop)
            that.$store.commit('setMainData', base)
            that.$store.commit('setDataList', lineData)
          }
          else{
            that.$d3.select(this).selectAll('.addFun').remove()
            that.$store.commit('setTagVisible', true)
            that.$store.commit('setTagID', d.target.__data__.id)
          }
        })

      node.filter(d => d.type == 'sample')
        .append('rect')
        .attr('width', d=>d.size)
        .attr('height', d=>d.size)
        .attr('fill', this.$dataMan.COLORS.other)
        .attr('stroke', d => {
          return d.id == this.suggestID ? 'red' : (d.status==0?this.$dataMan.COLORS.unlabel:this.$dataMan.COLORS.labeled)
        })
        .attr('stroke-width', 5)
        .attr("stroke-dasharray", d => {
          switch (d.status) {
            case 0:
              return '3 1';
            case 1:
              return '0 0'
          }
        });

      node.filter(d => d.type != 'sample')
        .append('circle')
        .attr('r', d => {
          return sizeScale(d.size)
        })
        .attr('fill', d => {
          switch (d.type) {
            case 'PER':
              return this.$dataMan.COLORS.PER
            case 'LOC':
              return this.$dataMan.COLORS.LOC
            case 'ORG':
              return this.$dataMan.COLORS.TIME
          }
        })
        .attr('stroke', d => {
          return d.id == this.suggestID ? 'red' : (d.status==0?this.$dataMan.COLORS.unlabel:this.$dataMan.COLORS.labeled)
        })
        .attr('stroke-width', 2)
        .on('mouseover', function (e) {
          let node = that.$d3.select(e.target.parentNode)
          let circle = that.$d3.select(e.target)
          let data = Object.assign({}, circle.data()[0])
          let r = circle.attr('r')
          r = parseInt(r)
          that.$d3.select('.sample-view').selectAll('.addFun').remove()
          let operData = [
            {x:r+10, y:-16, color:"#ff2b00",text:"✕", tcolor:'#ffffff', data:data},
            {x:r+15, y:0, color:'#409eff', text:'↻', tcolor:'#ffffff', data:data},
            {x:r+8, y:16, color:"#ffffff", text:'🌐', tcolor: "#000000", data:data},]
          let nodeOper = node.selectAll('.operNode')
            .data(operData)
            .enter()
            .append('g')
            .attr('transform', d=>`translate(${d.x}, ${d.y})`)
            .attr('class', 'addFun')

          nodeOper.append('circle')
            .attr('r', 8)
            .attr('fill', d=>d.color)
            .attr('class', (d, i)=>{
              return i===0?"remove":(i===1?'change':'search')
            })

          nodeOper.append('text')
            .attr("fill", d=>d.tcolor)
            .text(d=>d.text)
            .style("font-size", "14px")
            .style("font-weight", "bold")
            .attr('x', -5)
            .attr('y', 5)
            .style("pointer-events", "none")

        })

      node.append('text')
        .attr('fill', "#000000")
        .attr('font-size', 15)
        .style('cursor', 'pointer')
        .style('text-anchor', 'middle')
        .style('alignment-baseline', 'middle')
        .text(d => d.name)

      function start(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function drag(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function end(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      // 在模拟器中添加 tick 事件监听器
      simulation.on("tick", () => {
        node.attr("transform", d => {
          return `translate(${d.x}, ${d.y})`
        })
      });
    },
    drawHead() {
      let width = this.$d3.select(".chart-head").node().getBoundingClientRect().width;
      width = width - 10
      const svg = this.$d3.select('.chart-head')
        .append('svg')
        .attr('width', width)
        .attr('height', this.margin_top)
      let mark = [
        {name: 'sample', shape: 'rect', color: this.$dataMan.COLORS.other},
        {name: 'PER', shape: 'circle', color: this.$dataMan.COLORS.PER},
        {name: 'LOC', shape: 'circle', color: this.$dataMan.COLORS.LOC},
        {name: 'TIME', shape: 'circle', color: this.$dataMan.COLORS.TIME}
      ]
      let node = svg.selectAll('mark')
        .data(mark)
        .enter()
        .append('g')
        .attr('transform', (d, i) => {
          let y = this.margin_top / 2
          let x = 30 + (i + 1) * 70
          return `translate(${x}, ${y})`
        })
      node.filter(d => d.name == 'sample')
        .append('rect')
        .attr('y', -8)
        .attr('x', -8)
        .attr('width', 16)
        .attr('height', 16)
        .attr('fill', d => d.color)
      node.filter(d => d.name != 'sample')
        .append('circle')
        .attr('r', 8)
        .attr('fill', d => d.color)
      node.append('text')
        .attr('x', 10)
        .attr('y', 4)
        .text(d => d.name)
        .attr('font-size', 10)
      let border_data = [
        {type: 0, color: this.$dataMan.COLORS.labeled, text: 'labeled'},
        {type: 1, color: this.$dataMan.COLORS.unlabel, text: 'unlabel'},
        {type: 2, color: 'red', text: 'suggest'}
      ]
      let borderShape = svg.selectAll('.borderType')
        .data(border_data)
        .enter()
        .append('g')
        .attr('transform', (d, i) => {
          let begin = width / 5 * 3
          let y = this.margin_top / 2
          let x = begin + (i + 1) * 70
          return `translate(${x}, ${y})`
        })
      //添加虚线边框
      borderShape.append('circle')
        .attr('r', 8)
        .attr('fill', '#ffffff')
        .attr('stroke', d => d.color)
        .attr('stroke-width', 1)
        // .attr("stroke-dasharray", d => {
        //   switch (d.type) {
        //     case 0:
        //       return '0 0';
        //     case 1:
        //       return '5 5'
        //     case 2:
        //       return '5 5'
        //   }
        // });
      borderShape.append('text')
        .attr('x', 10)
        .attr('y', 4)
        .text(d => d.text)
        .attr('font-size', 10)
    },
    async nextTagLoop() {
      this.endTime = new Date()
      let timeSpan = this.$dataMan.timefig(this.endTime, this.beginTime)
      await this.$dataMan.insertTimeRecord(timeSpan)
      let netTagData = await this.$dataMan.getNextTagSample()
      let data = netTagData.data.res
      let dataList = netTagData.data.list
      let loop = netTagData.data.loop
      window.sessionStorage.setItem('loop', loop)
      this.$store.commit('setMainData', data)
      this.$store.commit('setDataList', dataList)
      this.$emit("mainDataChange")
      clearInterval(this.timer)
      this.beginTime = new Date()
      this.timer = setInterval(()=>{
        this.timeSpan = this.$dataMan.timefig(new Date(), this.beginTime)
      }, 1000)
    },
    tagSmp(item){
      this.$store.commit('setTagVisible', true)
      this.$store.commit('setTagID', item.id)
    },
    selectLS(){
      this.tagedIndexs = []
      this.$dataMan.getLoopSample(this.loop).then(res=>{
        console.log(res)
        let data = res.data.res
        let dataList = res.data.list
        let loop = res.data.loop
        window.sessionStorage.setItem('loop', loop)
        this.$store.commit('setMainData', data)
        this.$store.commit('setDataList', dataList)
        this.$emit("mainDataChange")
      })
    },
    // selectAction(){
    //   if(this.selector){
    //     let dom = document.querySelector('.select-box')
    //     let closeDom = document.querySelector('.select-icon')
    //     closeDom.style.display = "display"
    //     dom.style.display = "none"
    //     this.selector = false
    //   }else {
    //     let dom = document.querySelector('.select-box')
    //     dom.style.display = "display"
    //     this.selector = true
    //   }
    // },
    // drawBarChart(data) {
    //   data.sort((a, b) => {
    //     return this.strategy!='MNLP'?(a.LC - b.LC):(a.MNLP-b.MNLP)
    //   });
    //   data.forEach((item)=>{
    //     item.value = this.strategy!='MNLP'?item.LC:item.MNLP
    //     item.name = item.title
    //   })
    //   let min = this.strategy != 'MNLP'?data[0].LC:data[0].MNLP
    //   let max = this.strategy != 'MNLP'?data[data.length-1].LC:data[data.length-1].MNLP
    //   let colorScale = this.$d3.scaleLinear().domain([min, max]).range([0.7, 0.4])
    //   // eslint-disable-next-line no-undef
    //   const chart = echarts.init(document.getElementById('sample-list-chart'));
    //   const option = {
    //     xAxis: {
    //       show:false,
    //       type: 'value',
    //       axisLine: {show: false},
    //       axisTick: {show: false},
    //       axisLabel: {show: false}
    //     },
    //     yAxis: {
    //       show:false,
    //       type: 'category',
    //       data: data.map(item => item.name),
    //       axisLine: {show: false},
    //       axisTick: {show: false},
    //       axisLabel: {
    //         interval: 0,
    //         margin: 10
    //       },
    //       splitNumber:10,
    //     },
    //     grid: {
    //       top:'1%',
    //       bottom: '1%',
    //     },
    //     series: [{
    //       type: 'bar',
    //       data: data,
    //       itemStyle: {
    //         color: (e)=> {return this.$dataMan.COLORS.unlabel},
    //         // opacity: 0.7,
    //         emphasis: {
    //           // 设置鼠标悬停时的高亮效果
    //           color: this.$dataMan.COLORS.selected // 高亮时的颜色
    //         },
    //         opacity:0.7,
    //         borderRadius: [0, 3, 3, 0]
    //       },
    //       label: {
    //         show:true,
    //         position: 'inside',
    //         formatter: function(params) {
    //           return params.data.name.length <= 5 ? params.data.name:params.data.name.substring(0, 5)
    //         },
    //
    //       },
    //       barWidth:12,
    //       // barGap: 10,
    //       barCategoryGap: ['20%', '20%'],
    //       barBorderRadius: [10, 10, 10, 10]
    //       // barCategoryGap: '30%'
    //     }]
    //   };
    //
    //   chart.setOption(option);
    // },
    selectSampleData(id){
      let nodes = this.$d3.selectAll('.sample-node')
      nodes.attr('opacity', 1)
      nodes.filter(d=>d.id != id).attr('opacity', 0.3)
    },
    sampleListShow(){
      this.showList = true;
      // this.drawBarChart(this.$store.state.dataList)
    },
     tagNext(e){
      e.preventDefault();
      // if(key.code === 'Space'){
        let tag_id = -1
        if(this.tagedIndexs.length ===0 ){
          tag_id = this.$store.state.mainData[0].id
          this.tagedIndexs.push(this.$store.state.mainData[0].id)
        }
        for(let item of this.$store.state.mainData){
          if(this.tagedIndexs.indexOf(item.id) === -1){
            tag_id = item.id
            this.tagedIndexs.push(item.id)
            break
          }
        }
        ElMessage({
          message: h('p', { style: 'line-height: 1; font-size: 14px' }, [
            h('span', null, `已标：${this.tagedIndexs.length}`),
          ]),
        })
        if (tag_id === -1){
          this.$notice('error', '没有更多了')
          return
        }
        this.$store.commit('setTagVisible', true)
        this.$store.commit('setTagID', tag_id)
      // }
    },
    drawVolcanoContoursChart(){
      const n = vData.width;
      const m = vData.height;
      const width = 928;
      const height = Math.round(m / n * width);
      const path = this.$d3.geoPath().projection(this.$d3.geoIdentity().scale(width / n));
      const contours = this.$d3.contours().size([n, m]);
      const color = this.$d3.scaleSequential(this.$d3.interpolateTurbo).domain(this.$d3.extent(vData.values)).nice();

      const svg = this.$d3.select('#sample-view')
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;position: absolute;z-index:0;pointer-events: none");

      svg.append("g")
        .attr("stroke", "black")
        .selectAll()
        .data(color.ticks(20))
        .join("path")
        .attr("d", d => path(contours.contour(vData.values, d)))
        .attr("fill", color);
    }
  },
  watch: {
    '$store.state.mainData'(newVal, val) {
      this.$dataMan.suggestSample().then(res => {
        this.suggestID = res.data.res
        this.drawChart(newVal)
        // this.beginTime = new Date()
        // console.log(this.suggestID)
      })
    },
    '$store.state.dataList'(newVal){
      this.barData = newVal.sort((a, b)=>{
        return b.MNLP-a.MNLP
      })
      // if(this.$store.state.strategy != "Random")
      //   this.barData = newVal
    }
  },
}
</script>

<style scoped>
.sample-view {
  position: absolute;
  width: 100%;
  height: 99%;
  border-radius: 5px;
  overflow: hidden;
}

.chart-head {
  position: absolute;
  top: 0;
  width: 100%;
  height: 50px;
  z-index: 1
}

.chart-toolbox {
  position: absolute;
  width: 160px;
  height: auto;
  display: flex;
  flex-direction: column;
  left: 20px;
  bottom: 50px;
  font-size:14px;
}

.chart-box {
  position: relative;
  width: 100%;
  height: 60vh;
}

.sample-list-box {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 200px;
  height: 85%;
  right: 30px;
  /*top: 40px;*/
  bottom: 50px;
}

.sample-list {
  width: 100%;
  height: 93%;
  display: flex;
  flex-direction: column;
  overflow: auto;
  display: flex;
  cursor: pointer;
  z-index: 2;
  /*border: 1px solid;*/
}
#sample-list-chart{
  /*pointer-events: none;*/
  /*border: 1px solid;*/
  width: 100%;
  height: 99%;
  z-index: 0;
}
.submit {
  width: 100%;
  position: absolute;
  display: flex;
  bottom: 0px;
}
.sample-list-item{
  border: 1px solid #909399;
  background-color: #909399;
  border-radius: 2px;
  width: 92%;
  min-height: 15px;
  margin-bottom: 2px;
  text-align: center;
  font-size: 10px;
  white-space: nowrap;        /* 不换行 */
  overflow: hidden;           /* 隐藏溢出内容 */
  text-overflow: ellipsis;
  color: #f5f7fa;
}
.sample-list-item:hover{
  background-color: #42b983;
}
.time-view{
  position: absolute;
  bottom: 10px;
  left: 50%;
  font-family:"华文彩云";/*设置字体*/
  font-size:20px; /*设置字体大小*/
  font-weight:bolder; /*设置字体粗细*/
  -webkit-text-stroke:1px red;        /*文字描边*/
  -webkit-text-fill-color:transparent;    /*设置文字的填充颜色*/
}
.select-box{
  position: absolute;
  display: flex;
  top: 10%;
  flex-direction: column;
  width: 150px;
  border: 2px solid #f5f4f1;
  border-radius: 4px;
  z-index: 9;
}
.select-box>div{
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}
.select-box input{
  width: 90px;
  height: 20px;
  border: 1px solid #d3d3d3;
  border-radius: 4px;
}
.select-box span{
  width: 50px;
}
.select-box button{
  width: 150px;
  border: none;
}
</style>
<style scoped>
.el-slider{
  --el-slider-button-size: 15px;
}
</style>