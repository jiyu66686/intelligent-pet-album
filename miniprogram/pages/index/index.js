const app = getApp()
const API_BASE = 'https://your-domain.com/api'

Page({
  data: {
    photos: [],
    totalPhotos: 0,
    catCount: 0,
    dogCount: 0
  },

  onLoad() {
    this.loadPhotos()
    this.loadStats()
  },

  loadPhotos() {
    wx.request({
      url: `${API_BASE}/photos`,
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      success: (res) => {
        if (res.data.items) {
          this.setData({ photos: res.data.items.slice(0, 8) })
        }
      }
    })
  },

  loadStats() {
    wx.request({
      url: `${API_BASE}/statistics`,
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      success: (res) => {
        this.setData({
          totalPhotos: res.data.total_photos || 0,
          catCount: res.data.cat_count || 0,
          dogCount: res.data.dog_count || 0
        })
      }
    })
  },

  goToUpload() {
    wx.navigateTo({ url: '/pages/upload/upload' })
  },

  goToProfile() {
    wx.navigateTo({ url: '/pages/profile/profile' })
  },

  goToPhotos() {
    wx.showToast({ title: '查看全部照片', icon: 'none' })
  },

  viewPhoto(e) {
    const id = e.currentTarget.dataset.id
    wx.previewImage({
      urls: [this.data.photos.find(p => p.id === id)?.photo_url]
    })
  }
})