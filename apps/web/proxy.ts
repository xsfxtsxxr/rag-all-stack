import { auth } from './lib/auth'

/** Next 16 proxy 文件约定（替代 middleware）：管理后台需要登录 */
export default auth

export const config = {
  matcher: ['/admin/:path*'],
}
