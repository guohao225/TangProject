import { createApp } from 'vue'
import App from './App.vue'
// import HeyUI from 'heyui';
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import DataMan from "@/utils/DataMan";
import {notice} from "@/utils/DataMan";
import * as d3 from "d3"
import store from '@/store'
import recorder from "@/utils/ReCorder";
import setting from "../setting";

let app = createApp(App)
app.config.globalProperties.$dataMan = DataMan
app.config.globalProperties.$notice = notice
app.config.globalProperties.$d3 = d3
app.config.globalProperties.$recorder = recorder
app.use(ElementPlus)
app.use(store)
app.mount('#app')
