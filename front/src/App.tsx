import { useState } from 'react'
import { Button } from "@/components/ui/button"

function App() {

    const [count, setCount] = useState<number>(0)
  return (
    <>
     <Button className="text-red-700" onClick={() => setCount((count) => count + 1)}>Click me</Button>
        {count}
    </>
  )
}

export default App
