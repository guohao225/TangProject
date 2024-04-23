<template>
  <div style="text-align: center">
    <div style="font-size: 20px;font-weight: bold;margin-bottom: 10px">{{ sampleData ? sampleData.title : '' }}</div>
    <span>{{ sampleData ? sampleData.author : '' }}</span>
  </div>
  <div id="content-box">
    <div style="width: 100%;height: 100%;position: relative">
      <mark-box @down="showMark=false"
                @queryWord="queryWord"
                ref="markBox"
                id="poet-mark-box"
                v-show="showMark"></mark-box>
      <div class="tagger-toolbar">
        <el-button type="primary" :icon="Monitor" circle size="small" @click="getDicData(1)"/>
        <el-button type="primary" :icon="Notebook" circle size="small" @click="getDicData(2)"/>
        <el-button type="primary" :icon="HelpFilled" circle size="small" @click="embedChinaPoem"/>
<!--        <el-button type="primary" :icon="HelpFilled" circle size="small" @click="embedChinaPoem"/>-->
      </div>
      <p id="content"
         @mousedown="selctStart"
         @mousemove="selectMove"
         @mouseup='tagAction'
         @childClick="childEvent"
         @removeTag="removeTag"
         style="line-height: 2em;font-size: 25px"
      >no data</p>
      <el-button @click="tagDown" size="large">down</el-button>
      <el-button @click="tagUp" size="large">down</el-button>
    </div>
    <div id="poem-tip"
         v-loading="isQueryNote"
         element-loading-text="querying..."
    >
      <div v-if="isQueryWord" style="display: flex;">
        <iframe :src="queryWordUrl" width="99%" height="500" style="border: none;"></iframe>
        <iframe v-if="queryWordUrlHnadian.length" :src="queryWordUrlHnadian" width="99%" height="500" style="border: none;"></iframe>
      </div>

      <pre v-else>
           {{ poemNote }}
      </pre>
    </div>
  </div>
  <div class="fun">

    <el-button @click="$store.state.tagVis=false" size="large">cancel</el-button>
  </div>
</template>

<script>
import {getSpanStyle} from "@/tagbox";
import markBox from "@/components/MarkBox.vue";
import {Notebook, Monitor, HelpFilled, Loading} from "@element-plus/icons-vue";

export default {
  name: "tagger",
  props:["poemId"],
  watch:{
    '$store.state.tagID':{
      deep:true,
      immediate: true,
      handler: function(val){
        this.getData(val)
      }
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
      dialogWidth: "30%",
      poemTipSrc: "https://baidu.com/",
      poemNote: "",
      isQueryNote: false,
      isQueryWord: false,

      queryWordUrl: "https://dict.baidu.com/",
      queryWordUrlHnadian:"https://dict.baidu.com/",
      querySentenceUrl:'https://www.gushici.net/chaxun/ju/'
    }
  },
  methods: {
    closeAction() {
      this.$store.commit('setTagVisible', false)
      this.$store.commit('setTagID', -1)
    },
    getData(id) {
      this.$dataMan.getTagSample(id).then(res => {
        this.sampleData = res.data.res
        // console.log(this.sampleData)
        this.setLable()
        // this.embedChinaPoem()
      })
    },
    //初始加载时，设置标签
    setLable() {
      let dom = document.getElementById('content')
      dom.innerHTML = this.sampleData.content
      let entity_pos = this.sampleData.entity
      let content = this.sampleData.content
      dom.setAttribute('data-sampleID', this.sampleData.id)
      let sentence_slice = []
      let last_pos = 0
      if (entity_pos.length === 0) {
        dom.innerHTML = content
      } else {
        entity_pos.forEach((item, i) => {
          let str = getSpanStyle(item[0],
            [this.$dataMan.COLORS.PER, this.$dataMan.COLORS.LOC, this.$dataMan.COLORS.TIME, this.$dataMan.COLORS.other],
            content.slice(item[1], item[2] + 1),
            `${item[1]},${item[2]}`
          )
          sentence_slice.push(content.slice(last_pos, item[1]))
          sentence_slice.push(str)
          last_pos = item[2] + 1
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
      }
    },
    tagDown() {
      //获取标注序列
      let labels = this.updateLabel()
      let request = {
        id: this.sampleData.id,
        label: labels,
      }
      this.$emit('updateChart')
      let operations = this.$recorder.record
      this.$dataMan.tagUpdate(request).then(res => {
        let code = res.data.res
        if (code == 0)
          this.$notice('error', 'update filed')
        else {
          this.$notice('success', 'update success')
          this.$store.commit('setTagVisible', false)
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
          let text = child.nodeValue
          for (let i = 0; i < text.length; i++) {
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
      this.$recorder.addRecord([type, parseInt(pos[0]), parseInt(pos[1])], text, "", "", 2, parseInt(sampleID),
        parseInt(window.sessionStorage.getItem('loop')))
    },
    getDicData(type) {
      let text = this.sampleData.content
      switch (type) {
        case 1:
          this.$dataMan.getModelText(text).then(res => {
            this.sampleData.entity = res.data.entity
            this.sampleData.label = res.data.label
            // console.log(this.sampleData)
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
      if(text.length > 3){
        this.queryWordUrl = `https://www.gushici.net/chaxun/ju/${text}`
        this.queryWordUrlHnadian = ""
        // this.queryWordUrl = `https://www.zdic.net/hans/${text}`
      }else{
        this.queryWordUrlHnadian = `https://www.zdic.net/hans/${text}`
        this.queryWordUrl = `https://dict.baidu.com/s?wd=${text}&device=pc&from=home`
      }
    },
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
  bottom: 5rem;
  display: flex;
}

.tagger-toolbar {
  position: absolute;
  top: -2rem;
  right: 1rem;
}

#poem-tip {
  position: relative;
  width: 100%;
  overflow: auto;
  height: 510px;
  background-color: #f1f1f1;
  border-radius: 5px;
  margin-bottom: 1rem;
  padding: 5px;
}

iframe {
  position: relative;
}
</style>