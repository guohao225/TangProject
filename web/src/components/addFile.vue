<template>
  <div>
    <el-upload
      method="get"
      :auto-upload="false"
      :show-file-list="false"
      :on-change="fileTransmit"
      accept=".json"
    >
      <el-icon :size="30">
        <upload-filled></upload-filled>
      </el-icon>
    </el-upload>
  </div>
</template>

<script>
import {UploadFilled} from '@element-plus/icons-vue'
import {ElNotification} from "element-plus";
import axios from "axios";

export default {
  name: "addFile",
  data() {
    return {
      dialogVisible: false,
      file: null,

      titleFiled: "title",
      authorFiled: 'author',
      contentFiled: 'content'
    }
  },
  components: {
    UploadFilled,
  },
  methods: {
    fileTransmit(file, filelist) {
      let filename = file.name
      var reader = new FileReader() //新建一个FileReader
      reader.readAsText(file.raw, 'UTF-8') //读取文件
      let _this = this
      reader.onload = async function (evt) { //读取文件完毕执行此函数
        let dataJson = JSON.parse(evt.target.result)
        let apiUrl = 'http://127.0.0.1:5000/load_source_data'
        axios.post(apiUrl, {json: dataJson, filename:filename.split('.')[0]}, {timeout: 5000}).then(data => {
          if (data.data.res == 1) {
            ElNotification({
              title: 'Success',
              message: `file upload success~~`,
              position: 'bottom-right'
            })
            _this.$emit('data-update')
          }
        })
      }
    },
  },
}
</script>

<style scoped>
</style>