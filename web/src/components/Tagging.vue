<template>
    <div class="tagging">
        <div class="poet-title">
            <h3 style="line-height: 20px;margin-top: 30px;margin-bottom: 0px">{{ title }}</h3>
            <h4 style="margin-top: 5px;">{{ author }}</h4>
        </div>
        <div class="tagging-poet">
<!--            <input class="icon-back" type="image" :src="back_icon" @click="change(index>0?index-1:0)"-->
<!--                   style="margin-right: 20px"/>-->
            <div class="poet-frame" id="poet-frame">
                <mark-box v-show="$store.state.markBoxVisible" id="poet-mark-box" ref="markBox"></mark-box>
                <p type="text" v-for="(sentence,item) in poet" :data-sentence-labels=label[item] @mouseover="em_dis(item)">{{ sentence }}</p>
            </div>
            <input class="icon-forward" type="image" :src="forward_icon" @click="change(index+1)"
                   style="margin-left: 10px"/>
        </div>
        <div class="tagging-transform">
            <el-button @click="updateLabels()">保存</el-button>
            <turn-to-box :page="index" :page-count="poemNum"></turn-to-box>
            <el-button @click="rollback" :disabled="this.$store.state.isSave">取消更改</el-button>
        </div>
    </div>
</template>

<script>
import axios from "axios";
import back_icon from "@/assets/icon/back.png"
import forward_icon from "@/assets/icon/forward.png"
import markBox from "./MarkBox";
import pubsub from  'pubsub-js'
import {ElMessage} from "element-plus";
import turnToBox from "@/components/TurnToBox";

export default {
    name: "Tagging",
    data() {
        return {
            back_icon,
            forward_icon,

            title: "",
            author: "",
            poet: [],
            label: [],
            label_pos: [],
            index: 0,
            sdata: '',

            backup:{
              bPoet:[],
              bLabel:[],
              bLabelPos:[]
            },
            poemDiv: null,

            poemNum:0
        }
    },
    components: {
        markBox,
        turnToBox
    },
    mounted() {
        axios.post('http://127.0.0.1:5000/get_poem',{query:'_id',value:0}).then(data => {
            let poetdata = data.data.res[0]
            this.poet = poetdata[this.$config.fieldName.poem]
            this.title = poetdata[this.$config.fieldName.title]
            this.author = poetdata[this.$config.fieldName.author]
            this.label = poetdata["labels"]
            this.label_pos = poetdata['labels_pos']
            pubsub.publish('Trans', poetdata['translation'])

            //备份数据
            this.backup.bPoet = this.poet
            this.backup.bLabel = this.label
            this.backup.bLabelPos = this.label_pos

            this.poemDiv = document.getElementById('poet-frame')
            let _this = this

            let turn_btn = document.getElementById('turn-btn')
            turn_btn.addEventListener("click", this.turnToPage)
            /*
            * 处理选中文本的操作
            // * */
            this.poemDiv.addEventListener("mouseup", function (e) {
                let selection = window.getSelection()
                let range = selection.getRangeAt(0)
                if (range.startOffset == range.endOffset && range.startContainer == range.endContainer) {
                    _this.showMarkBox(false)
                    return
                } else {
                    _this.$refs.markBox.disable = true
                    _this.$refs.markBox.showBox(e,_this.poemDiv)
                }
            })
        })
        this.getToll()
        let _this = this
        pubsub.subscribe('SelectPoem',  (msg, data)=>{_this.change(data);console.log(data)})
    },
    updated() {
        this.initData(false)                    //页面更新时初始化页面
        for (let sp of this.$store.state.spans) {//为页面内的span绑定事件
            this.bindEvent(sp)
        }
        this.$store.state.spans = []
    },
    methods: {
        getToll(){
            axios.get("http://127.0.0.1:5000/get_message").then(res=>{
                let pData = res.data.poem_num
                this.poemNum = pData
            })
        },
        rollback(){
            let pItems = this.poemDiv.getElementsByTagName('p')
            for(let i = 0;i<pItems.length;i++){
                pItems[i].innerHTML = this.backup.bPoet[i]
            }
            this.label = this.backup.bLabel
            this.label_pos = this.backup.bLabelPos
            this.initData(true)
            this.$store.state.isSave = true
        },
        turnToPage(){
            let page = document.getElementById('turn-page')
            let pageContent = parseInt(page.value)
            this.change(pageContent)
        },
        em_dis(item){
            pubsub.publish("cur_sentence", item)
        },
        change(index) {
            axios.post("http://127.0.0.1:5000/get_poem",{query:'_id',value:index}).then(data=>{
                let pdata = data.data.res[0]
                this.author = pdata[this.$config.fieldName.author]
                this.title = pdata[this.$config.fieldName.title]
                this.poet = pdata[this.$config.fieldName.poem]
                this.label = pdata['labels']
                this.label_pos = pdata['labels_pos']
                this.index = index

                //备份数据
                this.backup.bPoet = this.poet
                this.backup.bLabel = this.label
                this.backup.bLabelPos = this.label_pos

                pubsub.publish('Trans', pdata['translation'])
                this.showMarkBox(false)

                this.$store.state.isUpdate = true
                this.$store.state.spanID = 0
                this.$store.state.currObj = []
                this.$store.state.spans = []
                this.$store.state.isChoooseSpan = false
            })
        },

        /*
        改变鼠标的状态
         */
        changeState(state) {
            this.$store.state.mouseState = state
        },

        getText(event) {
            this.showMarkBox(true)
            let markBox = document.getElementById('poet-mark-box')

            let x = event.layerX - 50
            let y = event.layerY + 25

            let scrollheight = this.poemDiv.scrollTop
            markBox.style.left = x + "px"
            markBox.style.top = y + scrollheight + "px"
        },

        showMarkBox(show) {
            this.$store.state.markBoxVisible = show
        },

        bindEvent(span) {
            let _this = this
            span.addEventListener('click', function (e) {
                _this.$store.state.currObj = []
                _this.$refs.markBox.showBox(e, _this.poemDiv)
                _this.$refs.markBox.disable = false
                _this.$store.state.currObj.push(span)
                _this.$store.state.currObj.push(span.parentElement)
                _this.$store.state.currObj.push(_this.poemDiv)
            })
            span.addEventListener('mouseenter', function () {
                window.getSelection().removeAllRanges()
            })
            span.addEventListener('selectstart', function (e) {
                e.preventDefault()
            })
        },
        /*
        初始化数据
         */
        initData(refresh) {
            if (this.$store.state.isUpdate||refresh) {
                let pElement = this.poemDiv.getElementsByTagName('p')
                let entity_pos = this.label_pos
                let entity_labels = this.label
                if (entity_pos.length == 0) {
                    return
                }
                let sentence = []
                let spanNum = 0
                this.$store.state.spanID = entity_pos.length
                for (let i = 0; i < entity_pos.length; i++) {
                    sentence = sentence.length > 0 ? sentence : this.poet[entity_pos[i][0]].split('')
                    let entityType = entity_labels[entity_pos[i][0]][entity_pos[i][1]]
                    let colorType = ''
                    switch (entityType) {
                        case 'B-PER':
                            colorType = this.$store.state.colorType.PER;
                            break
                        case 'B-LOC':
                            colorType = this.$store.state.colorType.LOC;
                            break
                        case 'B-ORG':
                            colorType = this.$store.state.colorType.ORG;
                            break
                    }
                    let spanID = 'tag-span' + i

                    let spanHtml = `<span id="${spanID}" class="tag-span" data-entity-type="${entityType}"
                           style="border: 3px solid; cursor: pointer; color: ${colorType}">`

                    sentence.splice(entity_pos[i][1] + spanNum, 0, spanHtml)
                    sentence.splice(entity_pos[i][2] + 1 + spanNum, 0, '</span>')

                    if (entity_pos.length > 1) {
                        if (i + 1 < entity_pos.length && entity_pos[i][0] == entity_pos[i + 1][0]) {
                            spanNum += 2
                            continue
                        } else {
                            pElement[entity_pos[i][0]].innerHTML = sentence.join('')
                            spanNum = 0
                            sentence = []
                        }
                    } else {
                        pElement[entity_pos[i][0]].innerHTML = sentence.join('')
                        sentence = []
                    }
                }

                let spanCollection = this.poemDiv.getElementsByClassName('tag-span')
                for (let sp of spanCollection)
                    this.$store.state.spans.push(sp)
            }
            this.$store.state.isUpdate = false
        },

        updateLabels(){
            let pHtmlCollection = this.poemDiv.getElementsByTagName('p')
            console.log(pHtmlCollection)
            let entityNum = 0
            let entity_pos = []
            let entitys = []
            let labels = []
            if(pHtmlCollection == undefined)return
            for(let i=0;i<pHtmlCollection.length;i++){
                let lable = pHtmlCollection[i].getAttribute('data-sentence-labels')
                lable = lable.split(',')
                this.label[i] = lable
                labels.push(lable)

                lable = lable.join('')
                lable = lable.replace(/B-(PER|LOC|ORG)/g,'B')
                lable = lable.replace(/I-(PER|LOC|ORG)*/g,'I')
                let re = /BI*/gi
                let res
                let temp = []
                while((res = re.exec(lable))!= null){
                    temp.push([i, res.index, res.index+res[0].length])
                    entity_pos.push([i, res.index, res.index+res[0].length])
                }
                if(temp.length>0){
                    for(let pos of temp){
                        entitys.push(this.poet[pos[0]].substring(pos[1], pos[2]))
                    }
                }
            }

            axios.post("http://127.0.0.1:5000/update",
                {
                    id:this.index,
                    labels:labels,
                    entity_pos:entity_pos,
                    entitys:entitys
                }).then(data=>{
                    let state = data.data['res']
                    pubsub.publish('UpdateEntity', state)
                    if(state) {
                        ElMessage({showClose: true, message: '保存成功', duration: 1000, type: 'success'})
                        this.$store.state.isSave = true
                    }
                    else
                        ElMessage({showClose: true, message: '保存失败', duration: 1000, type: 'error'})
            })

        },
    }
}
</script>

<style scoped>
.tagging {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
}

.tagging-poet {
    position: relative;
    display: flex;
    font-family: "Adobe 黑体 Std R";
    line-height: 30px;
    font-size: 20px;
    text-align: center;
    align-items: center;
    justify-content: center;
    overflow: auto;
    width: 100%;
    height: 70%;
}

.poet-title {
    text-align: center;
    height: 20%;
}

.poet-frame {
    position: relative;
    max-width: 80%;
    min-width: 70%;
    max-height: 99%;
    min-height: 60%;
    overflow: auto;
}

.sign_btn {
    position: absolute;
    top: 1%;
    left: 70%;
}

.icon-back {
    position: absolute;
    left: 2%;
}

.icon-forward {
    position: absolute;
    right: 2%;
}
.tagging-transform{
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 8%;
}
</style>