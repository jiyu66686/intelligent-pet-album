<template>
  <div class="photo-upload">
    <el-card>
      <template #header>
        <span>上传新照片</span>
      </template>

      <el-form :model="form" label-width="100px">
        <el-form-item label="选择照片">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="() => ElMessage.warning('请先移除已选文件')"
          >
            <el-button type="primary">选择图片</el-button>
            <template #tip>
              <div style="color: #999; font-size: 12px; margin-top: 5px;">
                支持 jpg / png / gif 格式，单张不超过 16MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="照片名称">
          <el-input v-model="form.photo_name" placeholder="给照片起个名字" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="添加一些描述" />
        </el-form-item>

        <el-form-item v-if="recognitionResult">
          <el-alert
            :title="`识别结果：${recognitionResult.pet_breed}（${recognitionResult.pet_type === 'cat' ? '🐱 猫咪' : '🐶 狗狗'}）置信度：${(recognitionResult.confidence * 100).toFixed(1)}%`"
            type="success"
            :closable="false"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleUpload" :loading="uploading" :disabled="!file">
            上传照片
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const uploadRef = ref()
const file = ref(null)
const uploading = ref(false)
const recognitionResult = ref(null)

const form = reactive({
  photo_name: '',
  description: ''
})

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
  recognitionResult.value = null
  if (!form.photo_name) {
    form.photo_name = uploadFile.name
  }
}

const handleUpload = async () => {
  if (!file.value) {
    ElMessage.warning('请选择要上传的照片')
    return
  }

  if (!form.photo_name) {
    ElMessage.warning('请输入照片名称')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('photo', file.value)
    formData.append('photo_name', form.photo_name)
    formData.append('description', form.description || '')

    const res = await api.post('/photos', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000
    })

    recognitionResult.value = res.recognition
    ElMessage.success(`✅ 上传成功！识别为：${res.recognition.pet_breed}`)

    setTimeout(() => {
      router.push('/photos')
    }, 3000)

  } catch (error) {
    console.error('上传失败:', error)
    // 🆕 显示后端返回的错误信息
    const msg = error.response?.data?.error || '上传失败，请重试'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
  }
}

const resetForm = () => {
  file.value = null
  uploadRef.value?.clearFiles()
  form.photo_name = ''
  form.description = ''
  recognitionResult.value = null
}
</script>

<style scoped>
.photo-upload {
  max-width: 600px;
  margin: 0 auto;
}
</style>