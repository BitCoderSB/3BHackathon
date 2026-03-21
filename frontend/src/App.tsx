import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import LivePanel from "./pages/LivePanel";
import ProductCatalog from "./pages/ProductCatalog";
import Analytics from "./pages/Analytics";
import Activity from "./pages/Activity";
import { useSocket, SocketContext } from "./hooks/useSocket";

function AppInner() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LivePanel />} />
        <Route path="/products" element={<ProductCatalog />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/activity" element={<Activity />} />
      </Route>
    </Routes>
  );
}

function App() {
  const socketState = useSocket();

  return (
    <SocketContext.Provider value={socketState}>
      <BrowserRouter>
        <AppInner />
      </BrowserRouter>
    </SocketContext.Provider>
  );
}

export default App;
