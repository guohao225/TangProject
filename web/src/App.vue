<template>
  <tagger v-if="taggingVis" @updateChart="updateMainChart"></tagger>
  <div class="common-layout" >
    <el-container class="main-page">
      <el-header class="header">
        <strong>{{language.title}}</strong>
<!--        <button @click="changeLanguage" data-type="EN" id="languageChange">EN</button>-->
      </el-header>
      <el-container>
        <el-aside class="aside" width="300px">
          <toolbar
            @InitDown="initWordFlow"
          ></toolbar></el-aside>
        <el-main style="padding-left: 15px;padding-right: 15px;padding-top: 0;">
          <div style="display: flex;width: 100%;height: 100%;flex-direction: column;">
            <div style="width: 100%;height: 100%;display: flex">
              <div style="width: calc(100% - 300px)">
                <view-title text="推荐样本视图"></view-title>
                <main-chart @mainDataChange="mainChange"></main-chart>
                <view-title text="实体记录视图"></view-title>
                <div style="display: flex; padding: 0">
                  <div style="height: 28vh; width: calc(100% - 100px)" class="entity-worldflow">no data</div>
                  <div style="display: flex;flex-direction: column;width: 2%; height: 10vh;margin-top: 10vh">
                    <el-button :disabled="wordFlowEpochMax <= 6"  :icon="aup" circle @click="changeWd('-')"/>
                    <div style="width: 50px;height: 50px;" @click="changeWd('-')"></div>
                    <div style="height: 50px;text-align: center">{{wordFlowEpochMax}}</div>
                    <el-button :disabled="wordFlowData.length<=wordFlowEpochMax" :icon="adown" circle @click="changeWd('+')"/>
                  </div>
<!--                  <div id='word-container' style="width: 400px;height: 100%">-->

<!--                  </div>-->
                </div>
              </div>
              <div style="width: 300px;margin-left: 1rem;display: flex;flex-direction: column">
<!--                <view-title text="标注视图"></view-title>-->
<!--                <tag-com></tag-com>-->
                <view-title text="标注结果记录视图"></view-title>
                <div class="label-record" style="height: 300px;width: 300px">
                  <span>标注耗时(分)</span>
                  <div id="labeltime"></div>
                  <span>未标注：已标注</span>
                  <div id="leavetolabel"></div>
                  <span>所有未标注：所有已标注</span>
                  <div id="all-leavetolabel"></div>
                  <span>实体类型占比</span>
                  <div id="ptoltot"></div>
                </div>
                <view-title text="模型结果记录视图"></view-title>
                <line-chart></line-chart>
              </div>
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>

  </div>
<!--  <dict-base-view v-else></dict-base-view>-->
</template>

<script>
import toolbar from './view/toolbar.vue';
import mainChart from "@/view/MainChart.vue";
// import history from "@/view/history.vue";
import tagger from "@/components/tagger.vue";
import lineChart from "@/components/lineChart.vue";
import {WordCloud, G2} from '@antv/g2plot';
import $ from "jquery";
import dictBaseView from "@/view/DictBaseView";
import {Burger, ArrowUp, ArrowDown} from "@element-plus/icons-vue";
import viewTitle from "@/components/ViewTitle";
import tagCom from "@/components/tagCom";
// import {range} from "../public/d3.v4.min";
// import data from '../public/data/data.json'
export default {
  name: 'App',
  components: {
    Burger,
    toolbar,
    mainChart,
    history,
    tagger,
    lineChart,
    dictBaseView,
    viewTitle,
    tagCom
  },
  data(){
    return{
      wordFlowEpoch:7,
      wordFlowEpochMax:7,
      dicbase:true,
      dialogVis:false,
      aup:ArrowUp,
      adown:ArrowDown,
      wordFlowData:[],
      flowRange:[0,1,2,3,4,5,6],
      wordCloudData:[],
      labeledToUnlabel:[],
      loopLabelToUnlabel:[],
      enittiesTypes:[],
      labelTime:[]
    }
  },
  computed:{
    taggingVis:function (){
      return this.$store.state.tagVis
    },
    language:function (){
      return this.$store.state.language
    }
  },
  mounted() {
    this.init()
    this.getData()
    if(localStorage.getItem('relation_total') == null){
      localStorage.setItem('relation_total', 0+'')
    }
  },
  watch:{
    wordFlowData(newV){
      let data = newV.length > 7? newV.slice(0, 7): newV
      this.initWordFlow(data)
    },
    wordCloudData(newV){
      this.drawWordCloud(newV)
    },
    loopLabelToUnlabel(newV){
      this.drawBars(newV, 'leavetolabel')
    },
    labeledToUnlabel(newV){
      this.drawBars(newV, 'all-leavetolabel')
    },
    enittiesTypes(newV){
      console.log(newV)
      this.drawBars(newV, 'ptoltot')
    },
    labelTime(newV){
      this.drawBars(newV, 'labeltime')
    }
  },
  methods:{
    async updateMainChart(){
      let data = window.sessionStorage.getItem('SelectSetting')
      data = JSON.parse(data)
      this.$store.commit('updateMainData', data)

      let l = await this.$dataMan.getLoopLabeledToUnlabel()
      this.loopLabelToUnlabel = l.data.res
    },
    getRecord(){
      this.$dataMan.getTrainRecord().then(res=>{
        this.$store.commit('setTrainRecord', [res.data.res, res.data.entity])
      })
    },
    async init(){
      // let localDtata = window.sessionStorage.getItem('SelectSetting')
      let res = await this.$dataMan.getSelectStatus()
      let state = res.data.res
      if(state){
        let cur = await this.$dataMan.getSelected()
        let base = cur.data.res
        let lineData = cur.data.list
        let loop = cur.data.loop
        window.sessionStorage.setItem('loop', loop)
        this.$store.commit('setMainData', base)
        this.$store.commit('setDataList', lineData)
      }
    },
    async getData(){
      let wd = await this.$dataMan.getLoopEntitys()
      this.wordFlowData = wd.data.res
      this.wordFlowData.forEach(item=>{item.date = ""+item.date})
      this.wordFlowData = this.wordFlowData.sort((a, b)=>{return a.date - b.date})
      this.wordFlowEpochMax = this.wordFlowData.length > 7? 6: this.wordFlowData.length-1
      let wordcdata = await this.$dataMan.getAllWordCloudData()
      this.wordCloudData = wordcdata.data.res
      //当前伦已标和未标
      let l = await this.$dataMan.getLoopLabeledToUnlabel()
      this.loopLabelToUnlabel = l.data.res

      let  l2 = await this.$dataMan.getAllLabelToUnlabel()
      this.labeledToUnlabel = l2.data.res

      let l3 = await this.$dataMan.getAllPERANDLOCANDTIME()
      this.enittiesTypes = l3.data.res

      let time = await  this.$dataMan.getLabelTime()
      this.labelTime = time.data.res
      //获取训练历史数据
      let train = await this.$dataMan.getTrainRecord()
      this.$store.commit('setTrainRecord', train.data.res)
    },
    updateData(){
      this.$dataMan.getSelected().then(res=>{
        let data = res.data.res
        let list = res.data.list
        let loop = res.data.loop
        let suggest = res.data.suggest
        window.sessionStorage.setItem('loop', loop)
        this.$store.commit('setMainData', data)
        this.$store.commit('setDataList', list)
      })
    },
    async initWordFlow(data){
      if(data.length ===0)return
      let dom = document.querySelector('.entity-worldflow')
      let width = dom.clientWidth
      let height = dom.clientHeight
      dom.innerHTML = ""
      let svg = this.$d3.select(".entity-worldflow").append('svg')
        .attr("width", width)
        .attr("height", height)
      let config = {
        topWord: 20,
        minFont: 15,
        maxFont: 30,
        tickFont: 12,
        legendFont: 12,
        colors:[this.$dataMan.COLORS.LOC, this.$dataMan.COLORS.PER, this.$dataMan.COLORS.TIME],
        curve: this.$d3.curveMonotoneX,
        width:width,
        height:height,
      };
      // eslint-disable-next-line no-undef
      wordstream(svg, data, config)
      svg.selectAll("#person").attr('fill', this.$dataMan.COLORS.PER)
      svg.selectAll("#time").attr('fill', this.$dataMan.COLORS.TIME)
      svg.selectAll("#location").attr('fill', this.$dataMan.COLORS.LOC)
      svg.select("#legend").selectAll("circle").attr('fill', (d, i)=>{
        return i===0?this.$dataMan.COLORS.LOC:(i===1?this.$dataMan.COLORS.PER:this.$dataMan.COLORS.TIME)
      })

      svg.select("#axisGroup").selectAll("text").text((d, i)=>{
        return this.flowRange[i]
      })
      svg.on('click', (e)=>{//contextmenu
        e.preventDefault()
        let target = e.target
        if(target.nodeName === 'text'){
          console.log(target.nodeName)
        }else {
          let mouseX = e.x-267.5
          let t = svg.selectAll("#xGridlinesGroup .tick").nodes().map((node)=>{
            let x = this.$d3.select(node).attr('transform')
            let begin = x.indexOf('(')
            let end = x.indexOf(',')
            x = x.slice(begin+1, end)
            return parseFloat(x)
          })
          let loopIndex = t.filter(item=>item<mouseX).length-1
          let wordChartData = data.filter(item=>item.date === ""+this.flowRange[loopIndex])[0]
          wordChartData = Object.assign({}, wordChartData.words)
          let loc = wordChartData.location.map(item=>{return {frequency:item.frequency, text:item.text, topic:'LOC'}})
          let per = wordChartData.person.map(item=>{return {frequency:item.frequency, text:item.text, topic:'PER'}})
          let tim = wordChartData.time.map(item=>{return {frequency:item.frequency, text:item.text, topic:'TIME'}})
          wordChartData = [...loc, ...per, ...tim]
          this.drawWordCloud(wordChartData)
        }

        // let target = e.target
        // if(target.nodeName !== 'text')return
        // let data = target.__data__
        // let imfo = data.id.split('#')
        // data = {text:data.text, loop:imfo[1], sampleID:imfo[2],
        //   pos:[imfo[0].split('_')[1], imfo[0].split('_')[2]]}
        // this.$store.commit('setFindOperationStatus', data)

      })
    },
    changeWd(oper){
      switch (oper){
        case '+':this.wordFlowEpochMax++;break;
        case '-':this.wordFlowEpochMax--;break;
      }
      if(this.wordFlowEpochMax >= 6){
        let min = this.wordFlowEpochMax - 6
        this.flowRange = []
        for(let i=min; i<=this.wordFlowEpochMax;i++){
          this.flowRange.push(i)
        }
        this.wordFlowData = this.wordFlowData.slice(min, this.wordFlowEpochMax+1)
      }
    },
    changeLanguage(){
      let btn = document.querySelector('#languageChange')
      let type = btn.getAttribute('data-type')
      if(type === 'EN'){
        btn.setAttribute('data-type', 'CH')
        btn.innerHTML = 'CH'
        this.$store.commit('changeLanguage', 0)
      }else{
        btn.setAttribute('data-type', 'EN')
        btn.innerHTML = 'EN'
        this.$store.commit('changeLanguage', 1)
      }
    },
    setSlider(range, data){
      let that = this;
      let max = range.length
      $("#wfslider").slider({
        range: true,
        min: 0,
        max: max,
        values: [0, 2],
        slide: function (event, ui) {
          // 更新折线图的可视范围
          // console.log(ui)
          if (ui.values[1] - ui.values[0] > 7) {
            ui.values[0] = ui.values[1] - 7
          }
          let range = []
          for (let i = ui.values[0]; i < ui.values[1]; i++) {
            range.push(i)
          }
          console.log(range)
          let lineData = data[0].slice(range[0], range[range.length - 1])
          let barData = data[1].slice(range[0], range[range.length - 1])
          // that.createNestingChart([lineData, barData], range)
        }
      });
    },
    mainChange(){
      this.getData()
    },
    drawWordCloud(data){
      let dom = document.getElementById('word-container')
      dom.innerHTML = ""
      let that = this
      const worldCloud = new WordCloud(dom, {
        data,
        wordField: 'text',
        weightField: 'frequency',
        wordStyle:{
          fontSize:[20,60]
        },
        color:(d)=>{
          let data = Object.assign({}, d.datum)
          let color = data.topic=="ORG"?"TIME":data.topic
          if(!color)return '#fff'
          return that.$dataMan.COLORS[color]
        }
      })
      worldCloud.render();
    },
    drawBars(data, domId){
      console.log(data)
      let isZero = data.every(item => item.value === 0)
      console.log(isZero)
      if(isZero){
        data = [{"name":"none", "value":99}]
      }
      let dom = document.getElementById(domId)
      dom.innerHTML = ""
      let width = dom.clientWidth
      let height = dom.clientHeight
      let count = 0
      let padding = 5
      data.forEach(item =>{count += item.value})
      let widthScale = this.$d3.scaleLinear().domain([0, count]).range([padding, width-padding])
      //绘制坐标轴
      var x = this.$d3.scaleLinear().domain([0, count]).range([padding, width-padding-1]);
      let svg = this.$d3.select(`#${domId}`)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
      svg.selectAll('.rect')
        .data(data)
        .enter()
        .append('rect')
        .attr('width', d=>widthScale(d.value)-padding-1)
        .attr('height', 20)
        .attr('fill', d=>{
          switch (d.name){
            case 'labeled':return this.$dataMan.COLORS.labeled;
            case 'unlabel':return this.$dataMan.COLORS.unlabel;
            case "PER":return this.$dataMan.COLORS.PER;
            case "ORG":return this.$dataMan.COLORS.ORG;
            case "LOC":return this.$dataMan.COLORS.LOC;
            case "TIME":return this.$dataMan.COLORS.TIME;
            case undefined:return this.$dataMan.COLORS.labeled;
            default:return this.$dataMan.COLORS.unlabel;
          }
        })
        .attr('x', (d, i)=>{
          if (i == 0)return padding
          let span = 0
          let preData = data.slice(0, i)
          preData.forEach(item =>{span += item.value})
          let x = widthScale(span)
          return x
        })
        .attr('y', 0)
        .on('mouseover', (e)=>{
          this.$d3.select(e.target).attr('fill', '#409eff')
        })
        .on('mouseleave', (e)=>{
          this.$d3.select(e.target).attr('fill', d=>{
            switch (d.name){
              case 'labeled':return this.$dataMan.COLORS.labeled;
              case 'unlabel':return this.$dataMan.COLORS.unlabel;
              case "PER":return this.$dataMan.COLORS.PER;
              case "ORG":return this.$dataMan.COLORS.ORG;
              case "LOC":return this.$dataMan.COLORS.LOC;
              case "TIME":return this.$dataMan.COLORS.TIME;
              default:return this.$dataMan.COLORS.unlabel;
            }
          })
        })

      let xaxis = svg.append('g').attr("transform", "translate(0, 20)").call(this.$d3.axisBottom(x).ticks(5));
      xaxis.selectAll(".domain")
        .style("display", "none")
        .style("dominant-baseline", "hanging")
      },
    tagNext(e){
      console.log(e)
    }
  }
}
</script>

<style>
.header{
  background-color: #384451;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #f1f1f1;
}
.aside{
  display: flex;
  flex-direction: column;
}
.common-layout{
  position: absolute;
  width: 99%;
  height: 99%;
  overflow: hidden;
}
.main-page{
  width: 100%;
  height: 100%;
  background: #ffffff;
  /*background: rgba(0,0,0,0.05);*/
}
.entity-worldflow{
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  margin-top: -7px;
}
#languageChange{
  position:absolute;
  right: 10px;
  top: 10px;
}
.label-record{
  display: flex;
  flex-direction: column;
  padding: 5px;
}
.label-record div{
  width: 100%;
  height: calc(100% / 4);
  overflow: visible;
}
</style>
