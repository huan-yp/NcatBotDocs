import { viteBundler } from '@vuepress/bundler-vite'
import { defineUserConfig } from 'vuepress'
import { plumeTheme } from 'vuepress-theme-plume'

export default defineUserConfig({
  // 请不要忘记设置默认语言
  blog: false,
  lang: 'zh-CN',
  head: [
    [
        'link', { rel: 'icon', href: '/images/logo.png' },
    ]
  ],
  locales: {
    '/': { lang: 'zh-CN', title: 'NcatBot 文档' }
  },
  theme: plumeTheme({
    hostname: 'http://docs.ncatbot.xyz',
    docsRepo: 'https://github.com/huan-yp/NcatBotDocs',
    docsBranch: 'master',
    docsDir: 'docs',
    plugins: {
      shiki: {
        languages: ['yaml', 'python', 'shell', 'json'],
      },
      markdownEnhance:{
        mermaid: true, // ✅ 启用 Mermaid 支持
      },
      comment: {
        provider: 'Giscus', // "Artalk“ | "Giscus" | "Twikoo" | "Waline"
        comment: true,
        repo: 'huan-yp/NcatBotDocs',
        repoId: 'R_kgDOP5C1xA',
        category: 'Announcements',
        categoryId: 'DIC_kwDOP5C1xM4CwTIS',
      },
      markdownPower: {
        imageSize: 'all', // 'local' | 'all'
        plot: true,
      },
    }
  }),
  bundler: viteBundler(),
})
