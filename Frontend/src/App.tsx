import { Route, Routes } from 'react-router'
import Navbar from './components/navbar'

// * Pages
import Homepage from "./pages/home"

export const ApiUrl = "http://10.20.1.19:5000";

function App() {
  if (!localStorage.getItem("lang")) localStorage.setItem("lang","en")
  if (localStorage.getItem("lang") != "en" && localStorage.getItem("lang") != "ar" && localStorage.getItem("lang") != "fr") localStorage.setItem("lang","en")

  return (
    <>
    <Navbar />
    <Routes>
      <Route index Component={() => <Homepage />} />
    </Routes>
    </>
  )
}

export default App
