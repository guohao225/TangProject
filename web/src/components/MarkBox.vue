<template>
  <div class="mark-box">
    <span class="triangle"></span>
    <el-button-group>
      <el-button type="primary" size="small" :color="$dataMan.COLORS.PER" @click="mark('PER')">P</el-button>
      <el-button type="primary" size="small" :color="$dataMan.COLORS.LOC" @click="mark('LOC')">L</el-button>
      <el-button type="primary" size="small" :color="$dataMan.COLORS.TIME" @click="mark('ORG')">T</el-button>
      <el-button type="primary" size="small" @click="mark('Q')">Q</el-button>
    </el-button-group>
  </div>
</template>

<script>
import {getSpanStyle} from "@/tagbox";

export default {
  name: "MarkBox",
  data() {
    return {
      disable: false,
      parentNode:null,
      curEvent:null,
    }
  },
  components: {},
  methods: {
    mark(type) {
      let pos = null
      let text = ""
      let contenDom = document.getElementById('content')
      let sampleID = contenDom.getAttribute('data-sampleID')
      if(type === 'Q'){
        let selection = window.getSelection();
        let range = selection.getRangeAt(0);
        let highlightedText = range.toString();
        this.$emit('queryWord', highlightedText)
        return;
      }
      if(this.curEvent.type == 'childClick'){
        let target = this.curEvent.detail.target
        let curType  = target.getAttribute('data-type')
        if(curType == type)
            return
        target.setAttribute('data-type',type)
        text = target.firstChild.nodeValue
        target.style.background = this.$dataMan.COLORS[type]
        target.childNodes[1].innerText = type
        pos = target.getAttribute('data-position').split(',')
        // this.$recorder.addRecord([curType, pos[0], pos[1]],text, [type, parseInt(pos[0]), parseInt(pos[1])],text,
        //   1,parseInt(sampleID), parseInt(window.sessionStorage.getItem('loop')))
      }else {
        let selection = window.getSelection();
        let range = selection.getRangeAt(0);
        text = range.toString();
        let span = document.createElement("span");
        range.surroundContents(span)
        pos = this.recordPosition(span)
        let spanHtml = getSpanStyle(type,
          [this.$dataMan.COLORS.PER, this.$dataMan.COLORS.LOC, this.$dataMan.COLORS.TIME, this.$dataMan.COLORS.other],
          text,
          `${pos[0]},${pos[1]}`
        )
        span.outerHTML = spanHtml
        //记录操作
        // this.$recorder.addRecord('',"", [type, pos[0], pos[1]], highlightedText,0,parseInt(sampleID),
        //   parseInt(window.sessionStorage.getItem('loop')))
      }
      this.$emit('down', [type, text, pos[0], pos[1]])
    },
    showBox(event, parentDiv) {
      this.curEvent = event;
      this.$store.state.markBoxVisible = true
      let markBox = document.getElementById('poet-mark-box')
      let x = event.type==='childClick'?(event.layerX+50):(event.layerX - 50)
      let y = event.type==='childClick'?(event.layerY+40):(event.layerY + 25)
      let scrollheight = parentDiv.scrollTop
      markBox.style.left = x + "px"
      markBox.style.top = y + scrollheight + "px"
      this.parentNode = parentDiv
    },
    recordPosition(child) {
      const textContainer = document.getElementById('content');
      let children = textContainer.childNodes
      let startPos = 0
      let endPos = 0
      for(let item of children){
        if(item !== child){
          switch (item.nodeName){
            case '#text':startPos += item.textContent.length;break;
            case 'SPAN':var cpos = item.getAttribute('data-position').split(',');
                        startPos+=(parseInt(cpos[1])+1-parseInt(cpos[0]));break;
          }
        }else {
          let content = item.childNodes[0].textContent
          endPos = startPos + content.length-1;
          break
        }
      }
      return [startPos, endPos]
    },
    queryWord(){
      this.$emit('queryWord')
    }
  }
}
</script>

<style scoped>
.triangle {
  position: absolute;
  left: 30px;
  top: -11px;
  width: 0px;
  height: 0px;
  border-top: 0px solid red;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-bottom: 10px solid darkgrey;
}

.triangle:after {
  position: absolute;
  content: "";
  width: 0px;
  height: 0px;
  border: 10px solid transparent;
  border-bottom-color: aliceblue;
  top: -8px;
  left: -10px;
}

.mark-box {
  display: flex;
  position: absolute;
  align-items: center;
  justify-content: center;
  z-index: 3;
  width: auto;
  height: 35px;
  padding: 5px;
  border: 2px solid darkgrey;
  border-radius: 5px 5px 5px 5px;
  background-color: aliceblue;
}

</style>