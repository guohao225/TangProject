<template>
  <div class="toolbar">
<!--    <h3>{{language.toolbar.title1}}</h3>-->
    <view-title :text="language.toolbar.title1"></view-title>
    <el-row align="bottom">
      <el-col :span="12">
        <div style="padding-bottom: 5px;">{{language.toolbar.upload}}</div>
      </el-col>
      <el-col :span="12">
        <add-file @data-update="dataListUpdate"/>
      </el-col>
    </el-row>
    <el-row align="bottom">
      <el-col :span="12">
        <div style="padding-bottom: 5px;">{{ language.toolbar.download }}</div>
      </el-col>
      <el-col :span="12">
        <el-icon :size="25" @click="exportTrain">
          <Download @click="download"/>
        </el-icon>
      </el-col>
    </el-row>
    <el-row align="middle">
      <el-col :span="12">
        数据
      </el-col>
      <el-col :span="12">
        <el-collapse>
          <el-collapse-item :title="curSelectData" :name="curSelectData">
            <ul>
              <li v-for="item in dataList" :key="item">
                <el-row>
                  <el-col :span="12">
                    <div @click="changeSelectData(item)">{{ item }}</div>
                  </el-col>
                  <el-col :span="12">
                    <el-button type="danger"
                               :icon="Delete"
                               size="small"
                               circle
                               @click="removeData(item)"
                    />
                  </el-col>
                </el-row>
              </li>
            </ul>
          </el-collapse-item>
        </el-collapse>
      </el-col>
    </el-row>
    <el-row align="bottom">
      <el-col :span="12">{{ language.toolbar.selectNum }}</el-col>
      <el-col :span="12">
        <el-input-number size="small" v-model="selectNum" :min="1"/>
      </el-col>
    </el-row>
    <el-row align="bottom">
      <el-col :span="12">{{ language.toolbar.strategy }}</el-col>
      <el-col :span="12">
        <el-select v-model="strategy" size="small" style="width: 120px" @change="saveStrage">
          <el-option
            v-for="item in strategyOptions"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </el-col>
    </el-row>
    <el-row>
      <div>
        <span>标签</span>
        <div style="width: 280px;height: 80px; overflow: auto;display: flex;
        border-radius: 4px;flex-wrap: wrap;padding: 5px;border: 2px solid #f5f4f1">
          <div v-for="item in labels" :key="item"
               style="border: 1px solid #d3d3d3;height: 30px;width: 90px;display: flex;
               justify-content: center;align-items: center;border-radius: 2px;margin-right: 5px">
            <el-tag :color="item.color" closable style="max-width: 50px">{{item.name}}</el-tag>
            <el-color-picker v-model="item.color" style="width: 20px"></el-color-picker>
          </div>
          <el-button :icon="Plus" style="background: #f5f7fa"/>
        </div>
      </div>
    </el-row>
    <el-row>
      <div>
        <span>关系标签</span>
        <div class="relation-box" style="width: 280px;height: 200px; overflow: auto;display: flex;
        border-radius: 4px;flex-wrap: wrap;padding: 5px;border: 2px solid #f5f4f1">
          <div v-for="item in relationTypes" :key="item"
               style="border: 1px solid #d3d3d3;height: 30px;width: 90px;display: flex;
               justify-content: center;align-items: center;border-radius: 2px;margin-right: 5px">
            <el-tag color="#fff" closable style="max-width: 100px" @close="removeRelations(item)">{{item}}</el-tag>
          </div>
          <el-button :icon="Plus" style="background: #f5f7fa" @click="relationAdd"/>
        </div>
      </div>
    </el-row>
    <el-row justify="end">
      <el-col :span="24">
        <el-button type="primary" @click="selectSetting" :style="{background:$dataMan.COLORS.buttons,border:'none'}">{{ language.toolbar.submit }}</el-button>
      </el-col>
    </el-row>
    <view-title :text="language.toolbar.title2"></view-title>
    <div class="data-statistic-box">
      <div class="data-pie-chart">
      </div>
      <div id="data-statistic">
    </div>

    </div>
  </div>
</template>

<script>
import addFile from '../components/addFile.vue';
import {Download, Delete, Timer, CirclePlus, Plus} from "@element-plus/icons-vue"
import {ElNotification} from "element-plus";
import viewTitle from "@/components/ViewTitle";
import {DonutChart} from "@/view/drawHistoryItem";

export default {
  setup() {

  },
  data() {
    return {
      dataList: [],
      Delete: Delete,

      curSelectData: '数据列表',
      selectNum: 1,

      strategy: 'LC',
      strategyOptions: ['LC', 'MNLP', 'Random', 'None'],

      sampleData :[],
      pieData :[],
      arcData:[],

      loop:1,
      time:new Date(),
      begain:0,
      end:0,

      Plus:Plus,
      relationTypes:[],

      labels:[{'name':'PER', color:this.$dataMan.COLORS.PER}, {'name':'LOC', color:this.$dataMan.COLORS.LOC},
        {'name':'TIME', color:this.$dataMan.COLORS.TIME}]

    }
  },
  computed:{
    language:function (){
      return this.$store.state.language
    },
  },
  components: {
    addFile,
    Download,
    Timer,
    CirclePlus,
    viewTitle
  },
  mounted() {
    this.getDataList()
    this.$dataMan.getRelations().then(res=>{
      this.relationTypes = res.data.res
      this.$dataMan.Relations = this.relationTypes
    })
    this.$dataMan.getSelectStatus().then(res=>{
      let status = res.data.res
      if(status == 1){
        this.getSamplesData()
      }
    })
    setInterval(this.updateTime, 1000)

    // this.updateTime()
  },
  watch:{
    sampleData:function (newV){
      let arcData = [{'name':'L', value:0, color:'hsl(100, 100%, 50%)'},{'name':'S', value:0,  color:'hsl(30, 100%, 50%)'},{'name':'U', value:0, color:'hsl(200, 100%, 50%)'}]
      newV.forEach(item=>{
        switch (item.clarity) {
          case 'labeled':arcData[0].value += 1;break;
          case 'selected':arcData[1].value +=1;break;
          case 'unlabel':arcData[2].value +=1;break;
        }
      })
      // console.log(this.sampleData)
      this.clearChart()
      this.drawDataStatistics(this.sampleData)
      this.drawPieChart(this.pieData, arcData)
    }
  },
  methods: {
    getDataList() {
      this.$dataMan.getDataList().then(res => {
        this.dataList = res.data.res
        if(this.dataList.length > 0){
          this.curSelectData = this.dataList[0]
        }
      })
    },
    dataListUpdate() {
      this.getDataList()
    },
    removeData(item) {
      this.$dataMan.removeData(item).then(res => {
        let result = res.data.res
        if (result == 0) {
          ElNotification({
            title: 'ERROR',
            message: "delete failed",
            position: 'bottom-right',
            type: 'error'
          })
        } else {
          this.$notice('success', 'delete success')
          this.getDataList()
        }
      })
    },
    selectSetting() {
      let request = {
        select_num: this.selectNum,
        data_name: this.curSelectData == "data" ? "" : this.curSelectData,
        strategy: this.strategy
      }
      this.$store.commit('setStrategy', this.strategy)
      sessionStorage.setItem('SelectSetting', JSON.stringify(request))
      this.$dataMan.setParameter(request).then(res => {
        let data = res.data.res
        let dataList = res.data.list
        let loop = res.data.loop
        this.getSamplesData()
        window.sessionStorage.setItem('loop', loop)
        this.$store.commit('setMainData', data)
        this.$store.commit('setDataList', dataList)
        this.$emit('InitDown')
      })
    },
    changeSelectData(item) {
      this.curSelectData = item
    },
    drawDataStatistics(data) {
      data.forEach(item=>{
        item.type = '1'
      })
      // console.log(data)
      let min = this.$d3.min(data, d=>d.score)
      let max = this.$d3.max(data, d=>d.score)
      let colorScale = this.$d3.scaleLinear().domain([min, max]).range([0.8, 0.5])
      // eslint-disable-next-line no-undef
      const chart = new G2.Chart({
        container: 'data-statistic',
        autoFit: true,
        theme:'classic'
      });
      chart.data(data);
      chart.coordinate('polar', {innerRadius:0.3});
      chart.axis('clarity', {
        grid:{
          show: true
        },
        title:null,
        label:null
      });
      chart.legend(false)
      chart
        .point()
        .adjust('jitter')
        .position('clarity*score')
        .color('clarity*score', (val, size)=>{
          switch (val){
            case "unlabel":return this.$dataMan.COLORS.unlabel
            case 'labeled':return this.$dataMan.COLORS.labeled
            case 'selected':return this.$dataMan.COLORS.suggest
          }
        })
        .shape('circle')
        .size(3)
        .style('sen_len', (val)=>{
          if(val > 200){
            return { lineWidth: 2, stroke: '#FA0710' };
          }
        })
      .tooltip('name*sen_len*score')

      chart.on('contextmenu',(e)=>{
        document.oncontextmenu = ()=>{
          return false
        }
        if(e.data == null)return
        let type = -1
        let id = -1
        if(e.data.data.clarity == 'labeled'){
          data.forEach(item=>{
            if(item.id == e.data.data.id) {
              item.clarity = 'unlabel'
              this.$dataMan.operateSample(item.id, 2)
            }
          })
        }
        if(e.data.data.clarity == 'unlabel'){
          data.forEach(item=>{
            if(item.id == e.data.data.id) {
              item.clarity = 'selected'
              this.$dataMan.operateSample(item.id, 0)
            }
          })
        }
        if(e.data.data.clarity == 'selected'){
          data.forEach(item=>{
            if(item.id == e.data.data.id)
            {item.clarity = 'unlabel'
            this.$dataMan.operateSample(item.id, 1)}
          })
        }
        this.$emit("sampleChange")
        chart.changeData(data);
      })
      chart.on('click',(e)=>{
        if(e.data == null)return
        this.$store.commit('setTagVisible', true)
        this.$store.commit('setTagID', e.data.data.id)
      })

      chart.render();
    },
    drawPieChart(data, sampleData){
      let dom = document.querySelector(".data-pie-chart")
      let width = dom.clientWidth
      let height = dom.clientHeight
      //
      // var color = this.$d3.scaleOrdinal()
      //   .range([this.$dataMan.COLORS.PER, this.$dataMan.COLORS.LOC, this.$dataMan.COLORS.TIME]);
      let svg = this.$d3.select('.data-pie-chart')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${width/2}, ${height/2})`)


      DonutChart(sampleData, {
        name: d => d.name,
        value: d => d.value,
        width: width,
        height: height,
        innerRadius: 22,
        outerRadius: 30,
        svg: svg,
        colors: [this.$dataMan.COLORS.labeled,this.$dataMan.COLORS.suggest, this.$dataMan.COLORS.unlabel]
      })
    },
    getSamplesData(){
      return this.$dataMan.getSampleStatistics().then(res => {
        // console.log(res)
        this.sampleData = res.data.res.sample
        this.pieData = res.data.res.entity
      })
    },
    clearChart(){
      let dom = document.querySelector('.data-pie-chart')
      dom.innerHTML = ""
      let dom1 = document.getElementById('data-statistic')
      dom1.innerHTML = ""
    },
    saveStrage(value){
      // console.log(value)
      this.$store.commit('setStrategy', value)
    },
    lookLoop(){
      let config = {
        select_num: this.selectNum,
        data_name: this.curSelectData == "data" ? "" : this.curSelectData,
        strategy: this.strategy
      }
      this.$dataMan.lookLoop(this.loop, config).then(res=>{
        let data = res.data.res
        let dataList = res.data.list
        let loop = res.data.loop
        this.$store.commit('setMainData', data)
        this.$store.commit('setDataList', dataList)
        // this.loop = loop
      })
    },
    updateTime(){
      this.time = new Date()
    },
    timeFormat(time){
      const date = new Date(time);
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');
      const formattedTime = `${hours}:${minutes}:${seconds}`;
      return formattedTime
    },
    timefig(a, b){
      a = new Date(a)
      b = new Date(b)
      const timeDifference = a.getTime() - b.getTime(); // 获取毫秒级时间差
      // 将毫秒转换为小时和分钟
      const minutesDifference = Math.floor((timeDifference / (1000 * 60)) % 60);
      return `${minutesDifference} minutes`
    },
    removeRelations(item){
      this.relationTypes = this.relationTypes.filter(elem => {
        return elem !== item
      })
      this.$dataMan.updateRelationTypes(this.relationTypes).then( res =>{
        this.relationTypes = res.data.res
      })
    },
    relationAdd(){
      let diag = prompt("输入关系类型名称：", "创建新关系")
      if(diag){
        this.relationTypes.push(diag)
        this.$dataMan.Relations = this.relationTypes
        this.$dataMan.updateRelationTypes(this.relationTypes).then( res =>{
          this.relationTypes = res.data.res
        })
      }
    }
  }
}
</script>
<style scoped>
.toolbar {
  width: 95%;
  height: auto;
  color: #000000;
}

.el-collapse-item__header {
  background-color: inherit;
}

.el-row {
  margin-bottom: 0.5rem;
}

#data-statistic {
  width: 100%;
  height: 300px;
}
.data-statistic-box{
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 350px;
}
.data-pie-chart{
  position: absolute;
  left: calc(50% - 30px);
  top: calc(50% - 30px);
  width: 60px;
  height: 60px;
}
</style>