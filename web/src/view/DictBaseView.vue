<template>
  <div class="dicbase-frame">
    <div class="tag-view">
      <el-button @click="tagUp">上一首</el-button>
      <tag-com @updateChart="updateList"></tag-com>
    </div>
    <div class="tag-sample">
      <ul v-infinite-scroll="load" class="infinite-list" style="overflow: auto">
        <li v-for="(i, index) in dataList" :key="i.id" class="infinite-list-item"
            :style="{background:i.labeled?'#8dc63f':'#00aeef'}"
            @click="listClick(i.id, index)">{{ i.title }}</li>
      </ul>
    </div>
    <div class="message">
      共标注:{{labeled}}
    </div>
  </div>
</template>

<script>
import tagCom from "@/components/tagCom";
export default {
  name: "DictBaseView",
  components:{
    tagCom,
  },
  data(){
    return{
      count:40,
      dataList:[],
      curPoemId:1,
      curPoem:0,
    }
  },
  computed:{
    labeled:function (){
      let data = this.dataList.filter(item=>{
        return item.labeled
      })
      return data.length
    }
  },
  mounted() {
    this.$dataMan.getPoemList().then(res=>{
      this.dataList = res.data.res
    })
  },
  methods:{
    load(){
      this.count += 2
    },
    listClick(id, index){
      this.$store.commit('setTagID', id)
      this.curPoem = index
    },
    updateList(){
      this.dataList[this.curPoem].labeled = true
      this.curPoem += 1
      this.$store.commit('setTagID', this.dataList[this.curPoem].id)
    },
    tagUp(){
      this.curPoem -= 1
      this.$store.commit('setTagID', this.dataList[this.curPoem].id)
    }
  }
}
</script>

<style scoped lang="less">
.dicbase-frame{
  position: absolute;
  width: 99%;
  height: 95%;
  display: flex;
  .tag-view{
    padding: 10px 10px 10px 10px;
    width: 80%;
    height: 100%;
    position: relative;
  }
  .tag-sample{
    width: 20%;
    height: 100%;
  }
  .message{
    position: absolute;
    bottom:1rem;
    color:red;
    font-size: 12px;
    font-weight: bold;
    z-index: 3;
  }
}
.infinite-list {
  height: 100%;
  padding: 0;
  margin: 0;
  list-style: none;
}
.infinite-list .infinite-list-item {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50px;
  //background: var(--el-color-primary-light-9);
  margin: 10px;
  //color: var(--el-color-primary);
}
.infinite-list .infinite-list-item + .list-item {
  margin-top: 5px;
}
</style>