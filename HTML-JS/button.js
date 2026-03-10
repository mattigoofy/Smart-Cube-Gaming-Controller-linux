var button = document.getElementById("button").addEventListener("click", clicked)

async function clicked() {
  await connect()
  console.log("connected")
}
