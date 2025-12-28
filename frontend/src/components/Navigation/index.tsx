import { Link, useLocation } from 'react-router-dom'

const Navigation = () => {
  const location = useLocation()

  const isActive = (path: string): boolean => {
    return location.pathname === path
  }

  const getLinkClasses = (path: string): string => {
    const baseClasses = 'px-4 py-2 rounded-md font-medium transition-colors'
    const activeClasses = 'bg-blue-600 text-white'
    const inactiveClasses = 'text-gray-700 hover:bg-gray-100'

    return `${baseClasses} ${isActive(path) ? activeClasses : inactiveClasses}`
  }

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">Trash Collection Routes</h1>
          </div>

          <div className="flex space-x-4">
            <Link to="/" className={getLinkClasses('/')}>
              View Routes
            </Link>
            <Link to="/create-route" className={getLinkClasses('/create-route')}>
              Create Route
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
