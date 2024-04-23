<template>
  <el-dialog :model-value="taggingVis"
             :width="dialogWidth"
             draggable
             :destroy-on-close="true"
             @keydown="keyAction"
             @contextmenu="mouseA"
             :before-close="closeAction"
             style="box-shadow: 2px 2px 5px darkgrey;border-radius:10px"
  >
    <template #header>
      <div style="text-align: center">
        <div style="font-size: 20px;font-weight: bold;margin-bottom: 10px">{{ sampleData ? sampleData.title : '' }}
        </div>
        <span>{{ sampleData ? sampleData.author : '' }}</span>
        <strong>{{total}}</strong>
      </div>
    </template>
    <div id="content-box">
      <div style="width: 100%;height: 100%;position: relative;display: flex">
        <div style="width: 50%">
          <mark-box @down="markDown"
                    @queryWord="queryWord"
                    ref="markBox"
                    id="poet-mark-box"
                    v-show="showMark"></mark-box>
          <div class="tagger-toolbar">
            <el-button type="primary" :icon="Monitor" circle size="small" @click="getDicData(1)"/>
            <el-button type="primary" :icon="Notebook" circle size="small" @click="getDicData(2)"/>
            <el-button type="primary" :icon="HelpFilled" circle size="small" @click="embedChinaPoem"/>
          </div>
          <p id="content"
             @mousedown="selctStart"
             @mousemove="selectMove"
             @mouseup='tagAction'
             @childClick="childEvent"
             @removeTag="removeTag"
             style="line-height: 2em;font-size: 25px;height: 300px;"
          ></p>
          <span>{{enNUm}}</span>
        </div>
        <div class="relation-tagger">

        </div>
        <el-dialog v-model="relationVis"
                   width="30%"
                   align-center
                   style="box-shadow: 2px 2px 5px darkgrey;border-radius:10px"
        >
          <div>
            <el-tag v-for="item in relationTypes" :key="item" @click="selectRelation(item)">
              {{ item }}
            </el-tag>
          </div>
        </el-dialog>
      </div>
      <div id="poem-tip" v-show="dialogWidth=='60%'"
           v-loading="isQueryNote"
           element-loading-text="querying..."
      >
        <iframe :src="queryWordUrl" v-if="isQueryWord" width="99%" height="300" style="border: none;"></iframe>
        <pre v-else>
           {{ poemNote }}
         </pre>
      </div>
    </div>
    <div class="fun">
      <el-button @click="tagDown">完成</el-button>
      <el-button @click="$store.state.tagVis=false">取消</el-button>
    </div>
  </el-dialog>
</template>

<script>
import {getSpanStyle} from "@/tagbox";
import markBox from "@/components/MarkBox.vue";
import {Notebook, Monitor, HelpFilled, Loading} from "@element-plus/icons-vue";

export default {
  name: "tagger",
  computed: {
    taggingVis: function () {
      let id = this.$store.state.tagID
      this.getData(id)
      return this.$store.state.tagVis
    },
    relationTypes: function () {
      return this.$dataMan.Relations
    },
    total:function () {
      return localStorage.getItem('relation_total')
    }

  },
  components: {
    markBox
  },
  data() {
    return {
      sampleData: null,
      showMark: false,
      selectTextStatus: -1,
      Notebook: Notebook,
      Monitor: Monitor,
      HelpFilled: HelpFilled,
      Loading: Loading,
      dialogWidth: "50%",
      poemTipSrc: "https://baidu.com/",
      poemNote: "",
      isQueryNote: false,
      isQueryWord: false,
      relations: [],
      connect: [],
      queryWordUrl: "https://dict.baidu.com/",
      relationVis: false,
      selectedRelation: "",
      enNUm:0,
    }
  },
  mounted() {
  },
  methods: {
    keyAction(e){
      if(e.code === 'Space'){
        this.tagDown()
      }
    },
    mouseA(e){
      e.preventDefault();
      this.tagDown()
    },
    closeAction() {
      this.$store.commit('setTagVisible', false)
      this.$store.commit('setTagID', -1)
    },
    getData(id) {
      this.$dataMan.getTagSample(id).then(res => {
        this.sampleData = res.data.res
        this.setLable()
        // console.log(this.sampleData)
      })
    },
    //初始加载时，设置标签
    setLable() {
      let dom = document.getElementById('content')
      dom.innerHTML = this.sampleData.content
      let entity_pos = this.sampleData.entity
      let content = this.sampleData.content
      this.drawForce()
      dom.setAttribute('data-sampleID', this.sampleData.id)
      let sentence_slice = []
      let last_pos = 0
      if (entity_pos.length === 0) {
        dom.innerHTML = content
      } else {
        entity_pos.forEach((item, i) => {
          let str = getSpanStyle(item[0],
            [this.$dataMan.COLORS.PER, this.$dataMan.COLORS.LOC, this.$dataMan.COLORS.TIME, this.$dataMan.COLORS.other],
            content.slice(item[2], item[3] + 1),
            `${item[2]},${item[3]}`
          )
          sentence_slice.push(content.slice(last_pos, item[2]))
          sentence_slice.push(str)
          last_pos = item[3] + 1
          if (i == entity_pos.length - 1 && last_pos != content.length) {
            sentence_slice.push(content.slice(last_pos, content.length))
          }
        })
        dom.innerHTML = sentence_slice.join('')
      }
      dom.setAttribute('data-label', this.sampleData.label)
    },
    tagAction(event) {
      if (this.selectText != 1) {
        this.selectText = -1
        this.showMark = false
        return
      }
      let selection = window.getSelection();
      let range = selection.getRangeAt(0);
      let highlightedText = range.toString();
      if (highlightedText.length > 0) {
        let contentDom = document.getElementById('content-box')
        this.showMark = true
        this.$refs.markBox.showBox(event, contentDom)

        //查询数据库中是否含有待标注的实体
        this.$dataMan.getEntityNum(highlightedText).then(res=>{
          this.enNUm = res.data.num
        })
      }

    },
    tagDown() {
      //获取标注序列
      let labels = this.updateLabel()
      let request = {
        id: this.sampleData.id,
        label: labels,
        relations:this.relations
      }
      let re_total = +localStorage.getItem('relation_total')+this.relations.length
      localStorage.setItem('relation_total',re_total+'')
      console.log(localStorage.getItem('relation_total'))
      let operations = this.$recorder.record
      this.$dataMan.tagUpdate(request).then(res => {
        let code = res.data.res
        if (code == 0)
          this.$notice('error', 'update filed')
        else {
          this.$notice('success', 'update success')
          this.$store.commit('setTagVisible', false)
          this.$emit('updateChart')
        }
      })
    },
    selctStart(event) {
      this.selectText = 0
    },
    selectMove(e) {
      if (this.selectText == 0) {
        this.selectText = 1
      }
    },
    updateLabel() {
      let text = document.getElementById('content')
      let children = text.childNodes
      let labels = []
      for (let child of children) {
        if (child.nodeName === 'SPAN') {
          let type = child.getAttribute('data-type')
          let entityText = child.firstChild.nodeValue
          entityText = entityText.replace(/\s+/g, '')
          for (let i = 0; i < entityText.length; i++) {
            if (i == 0) labels.push('B-' + type)
            else labels.push('I-' + type)
          }
        } else if (child.nodeName === 'SCRIPT') {
          continue
        } else {
          let textContent = child.nodeValue
          for (let i = 0; i < textContent.length; i++) {
            labels.push('O')
          }
        }
      }
      return labels
    },
    childEvent(e) {
      let contentDom = document.getElementById('content-box')
      this.showMark = true
      this.$refs.markBox.showBox(e, contentDom)
    },
    removeTag(e) {
      let contentDom = document.getElementById('content')
      let parent = e.detail.target.parentNode;
      let type = parent.getAttribute('data-type');
      let pos = parent.getAttribute('data-position').split(',');
      let sampleID = contentDom.getAttribute('data-sampleID')
      let text = parent.childNodes[0].textContent;
      text = text.replace(/\s+/g, '')
      let textNode = document.createTextNode(text);
      contentDom.replaceChild(textNode, parent)
      this.sampleData.entity = this.sampleData.entity.filter(item => item[2] !== parseInt(pos[0]))
      this.drawForce()
    },
    getDicData(type) {
      let text = this.sampleData.content
      switch (type) {
        case 1:
          this.$dataMan.getModelText(text).then(res => {
            this.sampleData.entity = res.data.entity
            this.sampleData.label = res.data.label
            this.setLable()
          });
          break;
        case 2:
          this.$dataMan.getDicData(text).then(res => {
            this.sampleData.entity = res.data.entity
            this.sampleData.label = res.data.label
            this.setLable()
          });
          break;
      }

    },
    embedChinaPoem() {
      this.isQueryWord = false
      this.isQueryNote = true
      this.dialogWidth = "60%"
      let text = this.sampleData.title + this.sampleData.author
      this.$dataMan.getPoemNote(text).then(res => {
        this.poemNote = res.data.res
        this.isQueryNote = false
      })
    },
    queryWord(text) {
      this.isQueryNote = false
      this.dialogWidth = "60%"
      this.isQueryWord = true
      this.queryWordUrl = `https://dict.baidu.com/s?wd=${text}&device=pc&from=home`
      // this.queryWordUrl = `https://search.cidianwang.com/?q=${text}&m=12&y=0`
      // this.queryWordUrl = `https://baike.baidu.com/item/${text}?fromModule=lemma_search-box`
    },
    drawForce() {
      let dom = document.querySelector('.relation-tagger')
      let width = dom.clientWidth
      let height = dom.clientHeight
      let nodeData = this.sampleData.entity.map(entity => {
        return {id: entity[2], name: entity[1], type: entity[0]}
      })
      // nodeData.unshift({id:-this.sampleData.author.length-1, name:this.sampleData.author, type:'PER'})
      function removeAllChildNodes(parentNode) {
        while (parentNode.firstChild) {
          parentNode.removeChild(parentNode.firstChild);
        }
      }
      removeAllChildNodes(dom)
      const svg = this.$d3.select(dom)
        .append('svg')
        .attr("viewBox", [0, 0, width, height])
        .attr('class', 'relation-force')

      const simulation = this.$d3.forceSimulation(nodeData)
        // .force("link", this.$d3.forceLink(this.relations).id(d => d[0]))
        .force("charge", this.$d3.forceManyBody().strength(-10))
        .force('center', this.$d3.forceCenter(width / 2, height / 2))
        .on('tick', ticked)

      const nodes = svg.selectAll(".nodes")
        .data(nodeData)
        .join("g")

      nodes.append('text')
        .text(d => d.name+""+d.id)
        .style('cursor', 'pointer')
        .attr('class', 'node')
        .style('text-anchor', 'middle')
        .style('alignment-baseline', 'middle')
        .attr('fill', d=>this.$dataMan.COLORS[d.type])
        .style('z-index', 4)
        .style('font-size', '20px')
        .style('font-weight','bold')
        .on('click', (e, d) => {
          this.connect.push(d)
          this.$d3.select(e.target).attr('stroke', this.$dataMan.COLORS.suggest)
          if (this.connect.length == 2) {
              this.relationVis = true
          }
        })

      function ticked() {
        nodes.attr("transform", d => `translate(${d.x},${d.y})`)
      }

      svg.on("click", (e) => {
        if (e.target.nodeName === 'svg') {
          this.connect = []
          svg.selectAll('.node').attr('stroke', "none")
        }
      })
    },
    async markDown(pos) {
      //关闭标注标签
      this.showMark = false
      //添加节点到力导向图中
      this.sampleData.entity.push(pos)
      this.drawForce()
    },
    selectRelation(item) {
      this.relationVis = false
      this.createLink(this.connect[0], this.connect[1], item)
      this.connect = []
    },
    createLink(node1, node2, type) {
      let that = this
      let svg = this.$d3.select('.relation-force');
      svg.selectAll('.node').attr('stroke', 'none');
      let bID = "#"+"p"+node2.id+"s"+node1.id
      let route = -10
      let bp = svg.select(bID)
      if(!bp.empty()) {
        route = 10
      }
      let control = { x: (node1.x + node2.x) / 2, y: (node1.y + node2.y) / 2 + route};
      // 创建贝塞尔曲线生成器
      let lineGenerator = this.$d3.line()
        .x(function(d) { return d.x; })
        .y(function(d) { return d.y; })
        .curve(this.$d3.curveBasis); // 选择曲线类型，比如基础曲线

      // 生成路径数据
      let pathData = lineGenerator([node1, control, node2]);

      svg.append("defs").append("marker")
        .attr("id", "arrow")
        .attr('class', "p"+node1.id+"s"+node2.id)
        .attr("viewBox", "0 0 10 10")
        .attr("refX", 9)
        .attr("refY", 5)
        .attr("markerWidth", 5)
        .attr("markerHeight", 5)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M 0 0 L 10 5 L 0 10 z")
        .attr("fill", "black");

      svg.append("path")
        .attr("d", pathData)
        .attr("stroke", "blue")
        .attr("stroke-width", 1)
        .attr("fill", "none")
        .style('z-index',3)
        .attr('class', "p"+node1.id+"s"+node2.id)
        .attr('id', "p"+node1.id + "s" + node2.id)
        .attr("marker-end", "url(#arrow)")


      let xOffset = -15
      let yOffset = -5
      if(route === 10){
        xOffset = 15
        yOffset = 5
      }
      let textCenter = [(node1.x + node2.x)/2+xOffset, (node1.y + node2.y)/2+yOffset]
      let slope = (node1.y-node2.y)/ (node1.x-node2.x)
      let rotationAngle = Math.atan(slope);
      svg.append('text')
        .attr('x', textCenter[0])
        .attr('y', textCenter[1])
        .attr('font-size',10)
        .style('cursor', 'pointer')
        .attr('class', "p"+node1.id+"s"+node2.id)
        .attr("transform", "rotate(" + (rotationAngle * 180 / Math.PI) + " " + textCenter[0] + " " + textCenter[1] + ")")
        .text(type)
        .on("dblclick", function(e, d){
          svg.selectAll(`.p${node1.id}s${node2.id}`).remove();
          that.relations = that.relations.filter(item=>{
            item.id !== that.sampleData.title+"_"+node1.id + "_" + node2.id
          })
        })
      //relation格式：{text:..., h:{name:..., pos:[]}, t:{name:..., pos:[]}, relation:..}
      this.relations.push({
        text:this.sampleData.content,
        h:{name:node1.name, pos:[node1.id, node1.id + node1.name.length]},
        t:{name:node2.name, pos:[node2.id, node2.id + node2.name.length]},
        relation:type,
        id:this.sampleData.title+"_"+node1.id + "_" + node2.id
      })
      console.log(this.relations)
    }
  }
}
</script>

<style scoped>
#content-box {
  width: 100%;
  height: auto;
  display: flex;
  flex-direction: column;
  position: relative;
}

.fun {
  position: absolute;
  right: 1rem;
  bottom: 10px;
  display: flex;
}

.tagger-toolbar {
  position: absolute;
  top: -2rem;
  right: 50%;
}

#poem-tip {
  position: relative;
  width: 100%;
  overflow: auto;
  height: 200px;
  background-color: #f1f1f1;
  border-radius: 5px;
  margin-bottom: 1rem;
  padding: 5px;
}

iframe {
  position: relative;
}

.relation-tagger {
  width: 50%;
  /*border-radius: 5px;*/
  margin-bottom: 1rem;
  height: 300px;
  border-left: 1px solid #384451;
  /*border: 1px solid #445469*/
}
</style>
