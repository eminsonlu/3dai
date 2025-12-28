import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { RouteMapContainer } from './containers/RouteMap'
import RouteCreator from './containers/RouteCreator'
import Navigation from './components/Navigation'

const App = () => {
  return (
    <BrowserRouter>
      <div className="w-full h-screen flex flex-col">
        <Navigation />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<RouteMapContainer />} />
            <Route path="/create-route" element={<RouteCreator />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
