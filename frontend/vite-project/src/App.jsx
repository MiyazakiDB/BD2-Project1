import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './Landing';
import Register from './Register';
import TLogin from './TLogin';
import NavigationBar from './NavigationBar';



export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<TLogin />} />
        <Route path="/register" element={<Register />} />
        <Route path="/navbar" element={<NavigationBar />} />
      
      </Routes>
    </BrowserRouter>
  );
}