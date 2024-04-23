<template>
  <div class="title" :style="{background:$dataMan.COLORS.title, color:$dataMan.COLORS.titleColor}">
    {{text}}
  </div>
</template>

<script>
export default {
  name: "title",
  props:['text']
}
</script>

<style scoped>
.title{
  position: relative;
  width: 100%;
  height: 25px;
  text-align: center;
}
</style>