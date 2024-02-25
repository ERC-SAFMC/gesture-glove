#ifndef UUID139747268226224
#define UUID139747268226224

#include <cstring>


namespace ContinousMotionPipeline {

    
        #ifndef UUID139747268217344
#define UUID139747268217344

/**
  * MinMaxScaler(low=0, high=1)
 */
class Step0 {
    public:

        /**
         * Transform input vector
         */
        bool transform(float *x) {
            
    for (uint16_t i = 0; i < 8; i++) {
        x[i] = (x[i] - offset[i]) * scale[i] + 0;

        if (x[i] < 0) x[i] = 0;
        else if (x[i] > 1) x[i] = 1;
    }

    return true;


            return true;
        }

    protected:
        
    float offset[8] = {-5087.00000000000f, -16171.00000000000f, -9877.00000000000f, -23900.00000000000f, -8269.00000000000f, -9429.00000000000f, -92.12000000000f, -29.96000000000f};
    float scale[8] = {0.00007412898f, 0.00004333319f, 0.00005088541f, 0.00001941295f, 0.00006627784f, 0.00006648052f, 0.00396825397f, 0.01525785780f};

};



#endif
    
        #ifndef UUID139747268228816
#define UUID139747268228816

/**
  * Window(length=90, shift=18)
 */
class Step1 {
    public:

        /**
         * Transform input vector
         */
        bool transform(float *x) {
            
    // append x to queue
    memcpy(queue + head, x, sizeof(float) * 8);
    head += 8;

    if (head != 720)
        return false;

    // copy queue to x and shift
    memcpy(x, queue, sizeof(float) * 720);

    
        memcpy(queue, queue + 144, sizeof(float) * 576);
    

    head -= 144;



            return true;
        }

    protected:
        
    uint16_t head = 0;
    float queue[720] = {0};

};



#endif
    
        #ifndef UUID139747268224256
#define UUID139747268224256

/**
  * SpectralFeatures(num_inputs=8, window_length=90, order=2, num_features=20)
 */
class Step2 {
    public:

        /**
         * Transform input vector
         */
        bool transform(float *x) {
            
    // spectral features
    uint16_t idx = 0;

    for (uint16_t k = 0; k < 8; k++) {
        float minimum = 9999999;
        float maximum = -9999999;
        float abs_minimum = 999999;
        float abs_maximum = 0;
        float mean = 0;
        float abs_energy = 0;
        float mean_abs_change = 0;
        float cid_ce = 0;
        float xi_prev = x[k];

        // first-order features
        for (uint16_t i = k; i < 720; i += 8) {
            float xi = x[i];
            float abs_xi = abs(xi);
            float xi_prev2 = (i >= k + 16) ? x[i - 16] : xi;

            float xi2 = xi * xi;
            float diff = xi - xi_prev;

            // start of features
            minimum = xi < minimum ? xi : minimum;
            maximum = xi > maximum ? xi : maximum;
            abs_minimum = abs_xi < abs_minimum ? abs_xi : abs_minimum;
            abs_maximum = abs_xi > abs_maximum ? abs_xi : abs_maximum;
            mean += xi;
            abs_energy += xi2;
            mean_abs_change += abs(diff);
            cid_ce += diff * diff;
            xi_prev = xi;
        }

        mean /= 90;
        abs_energy /= 90;
        mean_abs_change /= 90;
        cid_ce /= 90;

        buffer[idx++] = maximum;
        buffer[idx++] = minimum;
        buffer[idx++] = abs_maximum;
        buffer[idx++] = abs_minimum;
        buffer[idx++] = mean;
        buffer[idx++] = abs_energy;
        buffer[idx++] = mean_abs_change;
        buffer[idx++] = cid_ce;

        
            // second-order features
            float xi_mean_prev = x[k] - mean;
            float count_above_mean = 0;
            float count_below_mean = 0;
            float first_position_of_max = 720;
            float first_position_of_min = 720;
            float max_count = 0;
            float min_count = 0;
            float max_thresh = maximum - abs(maximum) * 0.02;
            float min_thresh = minimum + abs(minimum) * 0.02;
            float var = 0;
            float std = 0;
            float kurtosis = 0;
            float skew = 0;
            float has_large_std = 0;
            float variation_coefficient = 0;

            for (uint16_t i = k; i < 720; i += 8) {
                float xi = x[i];
                float xi_mean = xi - mean;
                float var_i = xi_mean * xi_mean;

                // start of features
                var += var_i;
                count_above_mean += xi_mean >  0.001 ? 1 : 0;
                count_below_mean += xi_mean < -0.001 ? 1 : 0;
                first_position_of_max = (i < first_position_of_max && abs(xi - maximum) < 0.001) ? i : first_position_of_max;
                first_position_of_min = (i < first_position_of_min && abs(xi - minimum) < 0.001) ? i : first_position_of_min;

                if (var_i > 0.001) {
                    skew += var_i * xi_mean;
                    kurtosis += var_i * var_i;
                }
                if (xi > max_thresh) { max_count += 1; }
                if (xi < min_thresh) { min_count += 1; }

                xi_mean_prev = xi_mean;
            }

            var /= 90;
            std = sqrt(var);
            first_position_of_max = int((first_position_of_max - k) / 90);
            first_position_of_min = int((first_position_of_min - k) / 90);
            skew = var > 0.001 ? skew / pow(var, 1.5) : 0;
            kurtosis = var > 0.001 ? kurtosis / (var * var) : 0;
            has_large_std = std > 0.25 * (maximum - minimum);
            variation_coefficient = (mean > 0.001) ? var / mean : 0;

            buffer[idx++] = std;
            buffer[idx++] = var;
            buffer[idx++] = count_above_mean;
            buffer[idx++] = count_below_mean;
            buffer[idx++] = first_position_of_max;
            buffer[idx++] = first_position_of_min;
            buffer[idx++] = max_count;
            buffer[idx++] = min_count;
            buffer[idx++] = has_large_std;
            buffer[idx++] = skew;
            buffer[idx++] = kurtosis;
            buffer[idx++] = variation_coefficient;
        
    }

    memcpy(x, buffer, 160 * sizeof(float));


            return true;
        }

    protected:
        
    float buffer[160];

};



#endif
    

     /**
      * Pipeline:
 * ---------
 *  > MinMaxScaler(low=0, high=1)
 *  > Window(length=90, shift=18)
 *  > SpectralFeatures(num_inputs=8, window_length=90, order=2, num_features=20)
     */
    class Pipeline {
        public:
            static const uint16_t NUM_INPUTS = 8;
            static const uint16_t NUM_OUTPUTS = 160;
            static const uint16_t WORKING_SIZE = 720;
            float X[720];

            /**
             * Apply pipeline to input vector
             */
            template<typename T>
            bool transform(T *x) {
                for (uint16_t i = 0; i < 8; i++)
                    this->X[i] = x[i];

                size_t start = micros();
                bool isOk =
                
                     step0.transform(X, X)
                
                    && step1.transform(X, X)
                
                    && step2.transform(X, X)
                ;

                latency = micros() - start;

                return isOk;
            }

            /**
             * Debug output feature vector
             */
            template<typename PrinterInterface>
            void debugTo(PrinterInterface &printer, uint8_t precision=5) {
                printer.print(X[0], precision);

                for (uint16_t i = 1; i < 160; i++) {
                    printer.print(", ");
                    printer.print(X[i], precision);
                }

                printer.print('\n');
            }

            /**
 * Get latency in micros
 */
uint32_t latencyInMicros() {
    return latency;
}

/**
 * Get latency in millis
 */
uint16_t latencyInMillis() {
    return latency / 1000;
}

        protected:
            float latency;
            
                ContinousMotionPipeline::Step0 step0;
            
                ContinousMotionPipeline::Step1 step1;
            
                ContinousMotionPipeline::Step2 step2;
            
    };
}


static ContinousMotionPipeline::Pipeline pipeline;


#endif