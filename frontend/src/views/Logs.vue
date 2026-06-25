<template>
  <div class="logs">
    <el-card>
      <template #header>
        <span>操作日志</span>
      </template>

      <el-table :data="logs" style="width: 100%;" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)">
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_table" label="目标表" width="120" />
        <el-table-column prop="target_id" label="目标ID" width="80" />
        <el-table-column prop="detail" label="详情" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

      <el-pagination
        v-model:page-size="perPage"
        v-model:current-page="currentPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const perPage = ref(20)

const getActionType = (action) => {
  const types = {
    'CREATE': 'success',
    'UPDATE': 'warning',
    'DELETE': 'danger',
    'QUERY': 'info',
    'LOGIN': 'info',
    'REGISTER': 'success'
  }
  return types[action] || ''
}

const loadData = async () => {
  try {
    const res = await api.get('/logs', {
      params: {
        page: currentPage.value,
        per_page: perPage.value
      }
    })
    logs.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>