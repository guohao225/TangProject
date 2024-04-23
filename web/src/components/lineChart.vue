<template>
  <div class="line-chart-box"
         element-loading-text="retraining..."
    >
    <div id="nesting-line-chart">

    </div>
    <div style="padding-left: 15px;padding-right: 15px;width: 90%;margin-bottom: 1rem">
      <el-slider v-model="cur_epoch" :max="max_epoch<7?8:max_epoch" :min="7" @change="changeChart"/>
    </div>
    <div class="loop-chart">
      no data
    </div>
  </div>
  <el-dialog
    v-model="centerDialogVisible"
    title="Finetuning"
    width="400px"
    destroy-on-close
    center
  >
    <el-row>
      <el-col :span="10"><span>epochs</span></el-col>
      <el-col :span="14">
        <el-input v-model="param.epochs"></el-input>
      </el-col>
    </el-row>
    <el-row>
      <el-col :span="10"><span>dropout</span></el-col>
      <el-col :span="14">
        <el-input v-model="param.dropout"></el-input>
      </el-col>
    </el-row>
    <el-row>
      <el-col :span="10"><span>regularize</span></el-col>
      <el-col :span="14">
        <el-input v-model="param.regularize"></el-input>
      </el-col>
    </el-row>
    <el-row>
      <el-col :span="10"><span>atn_regularize</span></el-col>
      <el-col :span="14">
        <el-input v-model="param.atn_regularize"></el-input>
      </el-col>
    </el-row>
    <el-row>
      <el-col :span="10"><span>learning_rate</span></el-col>
      <el-col :span="14">
        <el-input v-model="param.learning_rate"></el-input>
      </el-col>
    </el-row>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="centerDialogVisible = false">cancel</el-button>
        <el-button type="primary" @click="changeModelParam" :disabled="btnDisabled" :loading="btnLoading">
          confirm
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import $ from 'jquery'
import 'jquery-ui-dist/jquery-ui'
import 'jquery-ui-dist/jquery-ui.min.css'

export default {
  name: "lineChart",
  data() {
    return {
      active: false,
      inChart: false,

      lineData: [],

      centerDialogVisible: false,
      showContextMenu: false,

      param: {
        epochs: 20,
        dropout: 0.5,
        learning_rate: 0.001,
        regularize: 0.05,
        atn_regularize: 0.001,
      },
      curLoop: -1,

      loadData: false,
      btnDisabled: false,
      btnLoading: false,

      max_epoch:7,
      cur_epoch:7,
      line_data:[],
    }
  },
  watch: {
    '$store.state.trainRecord'(newV) {
      this.line_data = newV
      this.max_epoch = newV.length
      newV = newV.slice(0, 7)
      this.createNestingChart(newV, [0,1,2,3,4,5,6])
    }
  },
  mounted() {
    this.getData()
  },
  methods: {
    createNestingChart(data, range) {
      // let barData = data[1]
      // let op = barData.map(item => {
      //   return item.al + item.ap + item.at
      // })
      // console.log(op)
      // data = data[0]
      // let xRange = data.length
      let dom = document.getElementById('nesting-line-chart')
      let width = dom.clientWidth
      let height = dom.clientHeight
      dom.innerHTML = ""
      // 嵌套数据，其中每个点都有一个名字和一组子数据
      let that = this;
      // 定义画布大小和边距
      let margin = {top: 30, right: 10, bottom: 30, left: 30}
      width = width - margin.left - margin.right
      height = height - margin.top - margin.bottom
      // 定义 x 和 y 比例尺
      var x = this.$d3.scaleBand()
        .domain(range)
        .range([0, width])
        .padding(0.1);

      var y = this.$d3.scaleLinear()
        .domain([0, 1])
        .range([height, 0]);

      // var y2 = this.$d3.scaleLinear().domain([0, 200]).range([height, 0])

      // var line = this.$d3.line()
      //   .x(function(d, i) { return x(i); })
      //   .y(function(d, i) { return y2(d.al+d.ap+d.at);})
      //   .curve(this.$d3.curveCardinal)

      let childWidth = x.bandwidth() / 2
      let childHeight = x.bandwidth() / 2
      // 创建 SVG 元素
      var svg = this.$d3.select(`#nesting-line-chart`).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      // svg.append('path')
      //   .datum(barData)
      //   .attr('d', line)
      //   .attr("fill", "none")
      //   .attr("stroke", "red")
      //   .attr("stroke-width", 2)
      //
      // svg.selectAll('.text')
      //   .data(barData)
      //   .enter()
      //   .append('text')
      //   .text(d=>{
      //     let op = d.al+d.ap+d.at
      //     return op
      //   })
      //   .attr('x', (d, i)=>{return x(i)-10})
      //   .attr('y', d=>{return y2(d.al+d.ap+d.at)+10})
      //   .style('font-size', 10)

      // svg.selectAll('.circle')
      //   .data(barData)
      //   .enter()
      //   .append('circle')
      //   .attr('r', 2)
      //   .attr('cx', (d, i)=>{return x(i)})
      //   .attr('cy', d=>{return y2(d.al+d.ap+d.at)})

        // .attr('fill', "#ffffff")

      let chartsFrame = svg.selectAll('.lineChart')
        .data(data)
        .enter()
        .append('g')
        .attr('transform', d => {
          let ya = d.y
          // let ya = d.child[d.child.length - 1].y
          return `translate(${x(d.x) + childWidth / 2}, ${y(ya) - childHeight})`
        })
      chartsFrame.append(customNode)
        .attr('id', (d, i) => {
          return `linechart${i}`
        })
        .on('contextmenu', (e, d) => {
          let target = e.target
          let parent = target.parentNode
          let id = parent.getAttribute('id')
          id = parseInt(id.charAt(id.length - 1))
          // console.log(d)
          let data = {loop: id, sampleID: d.ids}
          // this.$store.commit('setFindOperationStatus', data)
          e.preventDefault()
          this.curLoop = id
          this.showMenu(e, data)
        })
        .on('mouseover', (e, d) => {
          this.active = true
          this.draLineChart(e, d)
        })
        .on('mouseout', (e, d) => {
          if (this.inChart) return
          this.active = false
        })
      chartsFrame
        .append("text")
        .text(d=>{
          let score = d.y
          return Number(score.toFixed(2))
        })
      .attr('x', 0)
      .attr('y', childHeight+10)
      .attr('font-size',10)
      .style('color', 'red')
      // 绘制 x 轴
      let xaxis = svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(this.$d3.axisBottom(x))
        .attr('stroke-width',2)
      xaxis.selectAll(".tick > line")
        .style("display", "none")
        .style("dominant-baseline", "hanging")
      xaxis.select('.domain').attr('stroke', this.$dataMan.COLORS.unlabel)

      // 绘制 y 轴
      let yaxis = svg.append("g")
        .call(this.$d3.axisLeft(y).ticks(3))
        .attr('stroke-width', 2)
      yaxis.select('.domain').attr('stroke', this.$dataMan.COLORS.unlabel)
      yaxis.selectAll(".tick > line")
        .style("display", "none")
        .style("dominant-baseline", "hanging")
      yaxis.append('text').attr('transform', 'rotate(-90)')
      .text("F1 Score")

      // 绘制 y 轴
      // svg.append("g")
      //   .attr('transform', `translate(${width-10}, 0)`)
      //   .call(this.$d3.axisRight(y2).ticks(5));
      //*************绘制柱状图**********************
      //高度比例尺
      // let heightScale = this.$d3.scaleLinear().domain([0, 20]).range([5, 15])
      // let barNodes = svg.selectAll('.entityBar')
      //   .data(barData)
      //   .enter()
      //   .append('g')
      //   .attr('transform', (d, i) => {
      //     let xOffset = (x.bandwidth() + 4) * i
      //     let yOffset = height
      //     return `translate(${xOffset}, ${yOffset})`
      //   })
      // function colorScale(color){
      //   var colorScale = that.$d3.scaleLinear()
      //     .domain([0, 100]) // 数据范围
      //     .range([color, '#FFFFFF'])
      //   // 根据数据值获取颜色
      //   var dataValue = 40;
      //   var scolor = colorScale(dataValue);
      //   // 调整颜色对比度
      //   var contrast = 0.8; // 对比度值（0-1之间）
      //   var adjustedColor = that.$d3.color(scolor);
      //   adjustedColor = that.$d3.interpolateRgb("#ffffff", adjustedColor)(contrast);
      //   return adjustedColor
      // }
      // barNodes.append('rect')
      //   .attr('width', x.bandwidth() / 3)
      //   .attr('height', d => heightScale(d.p))
      //   .attr('fill', this.$dataMan.COLORS.PER)
      // barNodes.append("rect")
      //   .attr('width', x.bandwidth()/3)
      //   .attr('height', d=>heightScale(d.ap))
      //   .attr('fill',  colorScale(this.$dataMan.COLORS.PER))
      // barNodes.append('rect')
      //   .attr('transform', `translate(${x.bandwidth() / 3}, 0)`)
      //   .attr('width', x.bandwidth() / 3)
      //   .attr('height', d => heightScale(d.l))
      //   .attr('fill', this.$dataMan.COLORS.LOC)
      // barNodes.append("rect")
      //   .attr('transform', `translate(${x.bandwidth() / 3}, 0)`)
      //   .attr('width', x.bandwidth()/3)
      //   .attr('height', d=>heightScale(d.al))
      //   .attr('fill', colorScale(this.$dataMan.COLORS.LOC))
      // barNodes.append('rect')
      //   .attr('transform', `translate(${x.bandwidth() / 3 * 2}, 0)`)
      //   .attr('width', x.bandwidth() / 3)
      //   .attr('height', d => heightScale(d.t))
      //   .attr('fill', this.$dataMan.COLORS.TIME)
      // barNodes.append("rect")
      //   .attr('transform', `translate(${x.bandwidth() / 3 * 2}, 0)`)
      //   .attr('width', x.bandwidth()/3)
      //   .attr('height', d=>heightScale(d.at))
      //   .attr('fill',colorScale(this.$dataMan.COLORS.LOC))

      // barNodes.selectAll('rect').on('click',(e, d)=>{
      //   console.log(d)
      // })
      //绘制内部折线图
      function customNode(selection) {
        let data = selection.epoch_val_f1
        // 定义 x 和 y 比例尺
        let x = that.$d3.scaleLinear()
          .domain([0, data.length - 1])
          .range([0, childWidth])

        let y = that.$d3.scaleLinear()
          .domain([0, 1])
          .range([childHeight, 0])

        var g = that.$d3.select(this)
        // 绘制曲线
        var line = that.$d3.line()
          .x(function (d, i) {
            return x(i)
          })
          .y(function (d) {
            return y(d)
          });
        // 绘制折线图
        let node = g.append('g')

        node.append('rect')
          .attr('width', childWidth)
          .attr('height', childHeight)
          .attr('fill', '#ffffff')

        node.append("path")
          .datum(data)
          .attr("fill", "none")
          .attr("stroke", that.$dataMan.COLORS.lines)
          .attr("stroke-width", 2)
          .attr("d", line)
          .style('pointer-event', 'none')
          .style('z-index', 1)

        // 绘制 x 轴
        node.append("g")
          .attr("transform", "translate(0," + childHeight + ")")
          .call(that.$d3.axisBottom(x)
            .ticks(0)
            .tickPadding(1)
            .tickSizeOuter(0)
          )
        // 绘制 y 轴
        node.append("g")
          .call(
            that.$d3.axisLeft(y)
              .ticks(0)
              .tickPadding(1)
              .tickSizeOuter(0)
          );
        return node.node()
      }

      svg.selectAll(".x-axis text")
        .style("text-anchor", "middle")
        .attr("y", -10); // 将标签向上移动一定距离
    },
    draLineChart(e, data) {
      let dom = document.querySelector('.loop-chart')
      let pos_x = e.layerX - 150
      let pos_y = e.layerY - 140
      dom.style.left = pos_x + "px"
      dom.style.top = pos_y + "px"
      dom.style.padding = '10'
      dom.style.background = "#ffffff"
      dom.style.border = "1px solid #f1f1f1"
      dom.style.borderRadius = "5px"
      dom.addEventListener('mouseover', (event) => {
        this.inChart = true
        this.active = true
      })
      dom.addEventListener('mouseout', (event) => {
        this.active = false
        this.inChart = false
      })
      // eslint-disable-next-line no-undef
      let chart = echarts.init(dom)
      //拆分数据集
      let x = []
      let y = []
      let loss = []
      data.epoch_val_f1.forEach((item, i) => {
        x.push(i+1)
        y.push(item)
      })
      let option = {
        xAxis: {
          type: 'category',
          data: x
        },
        yAxis: {
          type: 'value'
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '10%',
          top: '10%',
          containLabel: true
        },
        series: [
          {
            data: y,
            type: 'line',
            smooth: true,
            itemStyle:{
              color:this.$dataMan.COLORS.lines
            }
          }
        ]
      }
      option && chart.setOption(option);
    },
    showMenu(e, data) {
      let that = this
      this.showContextMenu = true
      this.$d3.select('.menu').remove()
      var menu = this.$d3.select('body').append('div')
        .attr('class', 'menu')
        .style('position', 'absolute')
        .style('left', e.pageX + 'px')
        .style('top', e.pageY + 'px')
        .style('display', 'flex')
        .style('flex-direction', 'column')
      let menuItem = ['operRecord', 'retrain']
      menu.selectAll('button')
        .data(menuItem)
        .enter()
        .append('button')
        .text(d => d)
        .style("background", '#fff')
        .style("border", 'none')
        .on('click', (e, d) => {
          console.log(e)
          console.log("点击了记录", d)
          switch (d) {
            case 'operRecord':
              this.$store.commit('setFindOperationStatus', data);
              break;
            case 'retrain':
              this.centerDialogVisible = true;
              break
          }
        })
        .on('mouseover', function () {
          console.log('over');
          that.$d3.select(this).classed('hover', true);
        })
        .on('mouseout', function () {
          that.$d3.select(this).classed('hover', false);
        });
      // 点击页面其他区域时移除菜单
      this.$d3.select('body')
        .on('click.menu', function () {
          menu.remove();
          that.$d3.select(this).on('click.menu', null);
        });
    },
    changeModelParam() {
      let request = {
        epochs: parseInt(this.param.epochs),
        dropout: parseFloat(this.param.dropout),
        learning_rate: parseFloat(this.param.learning_rate),
        regularize: parseFloat(this.param.regularize),
        atn_regularize: parseFloat(this.param.atn_regularize)
      }
      this.loadData = true;
      this.btnDisabled = true
      this.btnLoading = true
      this.$dataMan.changeModelParam(request, this.curLoop).then(res => {
        //更新散点图
        let intercalId = setInterval(() => {
          this.$dataMan.getTrainStatus().then(response => {
            if (response.data.res === 0) {
              //重新获取散点图的数据
              this.$dataMan.getTrainRecord().then(res => {
                this.$store.commit('setTrainRecord', [res.data.res, res.data.entity])
                clearInterval(intercalId)
                this.loadData = false
                this.centerDialogVisible = false
                this.btnDisabled = false
                this.btnLoading = false
              })
            }
          })
        }, 2000)

      })
    },
    getData() {
      this.loadData = true
      //重新获取散点图的数据
      // this.$dataMan.getTrainRecord().then(res => {
      //   this.$store.commit('setTrainRecord', [res.data.res, res.data.entity])
      //   this.loadData = false
      // })
    },
    changeChart(e){
      if(e-7 >= 0){
        let minStart = e-7
        let range = []
        for (let i = minStart; i < e; i++) {
          range.push(i)
        }
        console.log(minStart, e)
        let lineData = this.line_data[0].slice(minStart, e)
        let barData = this.line_data[1].slice(minStart, e)
        this.createNestingChart([lineData,barData], range)
      }
    }
}
}
</script>

<style scoped>
.line-chart-box {
  width: 100%;
  height: 60%;
  display: flex;
  position: relative;
  flex-direction: column;
  /*background-color: #f1f1f1;*/
}

#nesting-line-chart {
  width: 99%;
  height: 25vh;
}

.loop-chart {
  width: 99%;
  height: 30vh;
}

#slider {
  width: 90%;
  margin: auto;
}

.context-menu {
  position: absolute;
  display: flex;
  flex-direction: column;
  border: 1px solid;
}

.el-row {
  margin-bottom: 0.5rem;
}

.el-input {
  width: 200px;
}

.el-slider{
  --el-slider-button-size: 15px;
}
</style>