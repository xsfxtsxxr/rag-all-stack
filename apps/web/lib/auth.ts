import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'

/**
 * NextAuth v5 配置（Credentials 演示实现）。
 * 生产环境请接入 users 表并做密码哈希校验（如 bcrypt）。
 */
export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: 'jwt' },
  pages: { signIn: '/login' },
  providers: [
    Credentials({
      name: '账号密码',
      credentials: {
        email: { label: '邮箱', type: 'email' },
        password: { label: '密码', type: 'password' },
      },
      authorize: async (credentials) => {
        const email = typeof credentials?.email === 'string' ? credentials.email.trim() : ''
        const password = typeof credentials?.password === 'string' ? credentials.password : ''
        if (!email || password.length < 6) return null
        return { id: email, email, name: email.split('@')[0] ?? email }
      },
    }),
  ],
})
