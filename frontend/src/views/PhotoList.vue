<template>
  <div class="photo-list">
    <!-- 搜索和排序 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="8">
        <el-input v-model="search" placeholder="搜索照片..." @input="loadData" clearable>
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-col>
      <el-col :span="8">
        <el-select v-model="sort" placeholder="排序方式" @change="loadData">
          <el-option label="按时间排序" value="time" />
          <el-option label="按名称排序" value="name" />
          <el-option label="按点赞数排序" value="likes" />
        </el-select>
        <el-select v-model="order" placeholder="排序方向" @change="loadData" style="margin-left: 10px;">
          <el-option label="降序" value="desc" />
          <el-option label="升序" value="asc" />
        </el-select>
      </el-col>
      <el-col :span="8" style="text-align: right;">
        <el-button type="primary" @click="$router.push('/upload')">
          <el-icon><Upload /></el-icon> 上传照片
        </el-button>
        <el-button
          type="danger"
          @click="batchDelete"
          :disabled="selectedIds.length === 0"
        >
          <el-icon><Delete /></el-icon> 批量删除 ({{ selectedIds.length }})
        </el-button>
      </el-col>
    </el-row>

    <!-- 筛选标签（只保留猫咪和狗狗） -->
    <el-row style="margin-bottom: 15px;">
      <el-col>
        <el-radio-group v-model="petFilter" @change="loadData" size="small">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="cat">🐱 猫咪</el-radio-button>
          <el-radio-button label="dog">🐶 狗狗</el-radio-button>
        </el-radio-group>
      </el-col>
    </el-row>

    <!-- 照片网格 -->
    <el-row :gutter="20">
      <el-col
        :xs="12"
        :sm="8"
        :md="6"
        v-for="photo in photos"
        :key="photo.id"
        style="margin-bottom: 20px;"
      >
        <el-card class="photo-card" :body-style="{ padding: '0px' }">
          <div class="photo-checkbox">
            <el-checkbox
              :model-value="selectedIds.includes(photo.id)"
              @change="toggleSelect(photo.id)"
            />
          </div>
          <img :src="photo.photo_url" class="photo-image" @click="viewPhoto(photo.id)" />
          <div class="photo-info">
            <div>
              <div class="photo-name">{{ photo.photo_name }}</div>
              <div class="photo-breed">
                <el-tag :type="photo.pet_type === 'cat' ? 'success' : 'warning'" size="small">
                  {{ photo.pet_breed || '未知' }}
                </el-tag>
                <span class="confidence">置信度: {{ (photo.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div class="photo-actions">
              <el-button
                size="small"
                :type="photo.has_liked ? 'primary' : 'default'"
                @click="toggleLike(photo)"
              >
                <el-icon><Star /></el-icon> {{ photo.likes || 0 }}
              </el-button>
              <el-button size="small" @click="editPhoto(photo)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click="deletePhoto(photo.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <el-pagination
      v-model:page-size="perPage"
      v-model:current-page="currentPage"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="loadData"
      style="margin-top: 20px; justify-content: center;"
    />

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" title="编辑照片">
      <el-form :model="editForm">
        <el-form-item label="照片名称">
          <el-input v-model="editForm.photo_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Upload, Star, Edit, Delete } from '@element-plus/icons-vue'
import api from '../api'

const photos = ref([])
const total = ref(0)
const currentPage = ref(1)
const perPage = ref(12)
const search = ref('')
const sort = ref('time')
const order = ref('desc')
const petFilter = ref('')
const dialogVisible = ref(false)
const editForm = ref({ id: null, photo_name: '', description: '' })
const selectedIds = ref([])

const toggleSelect = (id) => {
  const index = selectedIds.value.indexOf(id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
}

const loadData = async () => {
  try {
    const res = await api.get('/photos', {
      params: {
        page: currentPage.value,
        per_page: perPage.value,
        sort: sort.value,
        order: order.value,
        search: search.value,
        pet_type: petFilter.value
      }
    })
    photos.value = res.items || []
    total.value = res.total || 0
    selectedIds.value = []
  } catch (error) {
    console.error('加载照片列表失败:', error)
  }
}

const viewPhoto = (id) => {
  const photo = photos.value.find(p => p.id === id)
  if (photo) {
    window.open(photo.photo_url, '_blank')
  }
}

const toggleLike = async (photo) => {
  try {
    let res
    if (photo.has_liked) {
      res = await api.post(`/photos/${photo.id}/unlike`)
      photo.has_liked = false
    } else {
      res = await api.post(`/photos/${photo.id}/like`)
      photo.has_liked = true
    }
    photo.likes = res.likes
  } catch (error) {
    const msg = error.response?.data?.error || '操作失败'
    ElMessage.warning(msg)
  }
}

const editPhoto = (photo) => {
  editForm.value = { id: photo.id, photo_name: photo.photo_name, description: photo.description }
  dialogVisible.value = true
}

const saveEdit = async () => {
  try {
    await api.put(`/photos/${editForm.value.id}`, {
      photo_name: editForm.value.photo_name,
      description: editForm.value.description
    })
    ElMessage.success('更新成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('更新失败:', error)
  }
}

const deletePhoto = (id) => {
  ElMessageBox.confirm('确定要删除这张照片吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await api.delete(`/photos/${id}`)
    ElMessage.success('删除成功')
    loadData()
  }).catch(() => {})
}

const batchDelete = () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的照片')
    return
  }
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedIds.value.length} 张照片吗？`,
    '批量删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const res = await api.post('/photos/batch-delete', {
        ids: selectedIds.value
      })
      ElMessage.success(`成功删除 ${res.success} 张照片`)
      selectedIds.value = []
      loadData()
    } catch (error) {
      ElMessage.error('批量删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.photo-card {
  cursor: pointer;
  transition: transform 0.2s;
  height: 340px;
  display: flex;
  flex-direction: column;
  position: relative;
}
.photo-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.photo-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 4px;
  padding: 2px 6px;
}
.photo-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
  flex-shrink: 0;
}
.photo-info {
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.photo-name {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.photo-breed {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 4px;
}
.confidence {
  font-size: 11px;
  color: #999;
}
.photo-actions {
  display: flex;
  gap: 5px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.photo-actions .el-button {
  padding: 4px 8px;
  font-size: 12px;
}
</style>