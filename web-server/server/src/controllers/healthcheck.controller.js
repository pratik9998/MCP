import { ApiError} from "../utils/ApiError.js"
import { asyncHandler } from "../utils/asyncHandler.js"
import { ApiResponse } from "../utils/ApiResponse.js" 

const healthcheck = asyncHandler (async (req, res) => {
    try {
        return res.status(200).json(new ApiResponse(200, {}, "server is running fine!!"))
    } catch (error) {
        throw new ApiError(400, `healthcheck failed : ${error}`)
    }
})

export { healthcheck }