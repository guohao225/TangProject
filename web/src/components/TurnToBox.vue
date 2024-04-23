<template>
    <div class = 'turnTo-frame'>
        <input class="turn-page" id="turn-page" type="number" maxlength="225" oninput="if (value>{pageCount})value=1000"/>
        <input class="turn-btn" id="turn-btn" type="image" :src="doubleRight"/>
        <p class="turn-page-msg" :data-page="page">第{{page}}页/{{pageCount}}</p>
    </div>
</template>

<script>
import doubleRight from "@/assets/icon/angle-double-right.png"
export default {
    name: "TurnToBox",
    props:{
        page:{
            required:true
        },
        pageCount:{
            required: true
        }},
    data(){
        return{
            doubleRight,

        }
    }
}
</script>

<style scoped>
.turnTo-frame{
    display: flex;
    height: 98%;
    align-items: center;
    justify-content: center;
}
.turn-btn{
    position: relative;
    background-color: #FFDEE9;
    background-image: linear-gradient(0deg, #FFDEE9 0%, #B5FFFC 100%);
    right: 28px;
    height: 80%;
}
.turn-page{
    outline: none;
    border-radius: 5px;
    border: 2px solid dodgerblue;
    width: 80px;
    height: 80%;
}
.turn-page-msg{
    position: relative;
    right: 20px;
}
</style>