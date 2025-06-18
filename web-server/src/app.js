import express, {json} from "express"
import cors from "cors"
import cookieParser from "cookie-parser"

const app = express()

app.use(cors({
    origin : process.env.CORS_ORIGIN,
    credentials : true
}))

app.use(express.json({limit : "16kb"}))  //frontend se jo json form ma data aayega uski max size
app.use(express.urlencoded({extended: true , limit: "16kb"}))  //url (encoded) se jo request aayegi uske liye
app.use(express.static("public")) //this stores some files in public folder at the backend server
app.use(cookieParser())

// import routes here
import healthcheckRouter from "./routes/healthcheck.route.js"

app.use("/api/v1/healthcheck", healthcheckRouter)

export {app}