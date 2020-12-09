#include "transilien.h"

#define TIME_CHANGE_SECONDS	10
#define TIMEOUT_ERROR 15

#define NUM_MAX7219     3

#define LED_STATUS	LATAbits.LATA3 //PORTAbits.RA3

#define HIGH 1
#define LOW 0
#define CS        PORTAbits.RA0
#define SERCLK    PORTAbits.RA1
#define DATA_bit  PORTAbits.RA2

#define PIN_DIRECTION PORTBbits.RB2
#define PIN_PUSH_INTERM PORTBbits.RB0

#define     ONE_S_TMR0H 0x67
#define     ONE_S_TMR0L 0x69

// function declarations
void ssrOut(unsigned char);
void pulseCS(void);
void init_MAX7219(void);
void writeMAX7219(char, char);
void writeMAX7219_3(char address1, char data1, char address2, char data2, char address3, char data3);

void delay_ms(int);
void delay_us(int);
void delay_1s(void);

void init_MCU(void);

unsigned char delayus_variable;

unsigned char waiting_for_timer = 0;
int8_t time_tick_flag = 0;
int8_t need_tx_time_delay = 0;
int8_t need_tx_dir_switch = 0;
int8_t need_tx_interm_toggle = 0;
int8_t num_quarter_hours_delay = 0;
int8_t button_interm_debounce = 0;
int8_t button_next_debounce = 0;
int8_t direction_bit = 0;
int8_t show_interm = 0;
int8_t timeout_err = TIMEOUT_ERROR;
        
//int i, j, digit, count;
int main_counter = 0;

//TIMECODE: HHMM
//FORMAT: CURTIME:TIMECODE-{TRAINNAME:CHAR-ARRIVE:TIMECODE-STATUS:CHAR[01234RS]-VOIE:CHARx2}x4
//static char DATA1[] = "1350D1359002H1410005D1411202H1415S00";
//static char DATA2[] = "1450D1459002H1515005D1521202H1525S00";

static char DATA_LOAD[] = "L--------002-----005-----002-----000";
static char DATA_PARI[] = "P--------002-----005-----002-----000";
static char DATA_BANL[] = "B--------002-----005-----002-----000";

char CURRENT_DATA[36] = {0};

//reply/request:
// DELTA: INT, DIR: BYTE [0 1]

const uint8_t MAX7219_LETTERS[] = {
//Bit: 76543210
//seg: pABCDEFG
	 0b01110111, //A
	 0b00011111, //b
	 0b01001110, //C
	 0b00111101, //d
	 0b01001111, //e
	 0b11111111, //f NOTIMPL
	 0b11111111, //g NOTIMPL
	 0b00110111, //H
	 0b00110000, //I
	 0b11111111, //J NOTIMPL
	 0b11111111, //K  NOTIMPL
	 0b11111111, //L NOTIMPL
	 0b11111111, //M  NOTIMPL
	 0b00010101, //n  NOTIMPL
	 0b11111111, //O NOTIMPL
	 0b01100111, //P  NOTIMPL
     0b11111111, //Q  NOTIMPL
	 0b00000101, //R  NOTIMPL
	 0b01011011, //S
	 0b00001111, //T
	 0b00011100, //u
	 0b11111111, //v NOTIMPL
	 0b11111111, //w NOTIMPL
};

const uint8_t MAX7219_DIGITS[] = {
//seg: pABCDEFG
	 0b01111110, //0
	 0b00110000, //1
	 0b01101101, //2
     0b01111001, //3
	 0b00110011, //4
	 0b01011011, //5
	 0b01011111, //6
	 0b01110000, //7
     0b01111111, //8
     0b01111011, //9
};

const uint8_t MAX7219_DASH = 1;

#define LETTER_B

#define DEC_AMOUNT 100


#include "transilien.h"
#include "system_config.h"
#include "app_custom_cdc.h"
#include <usb/usb.h>



#ifdef  COMPILER_MPLAB_C18                      // MCHP C18 comppiler
    void SYS_InterruptHigh();
    void SYS_InterruptLow();

    #pragma code HIGH_INTERRUPT_VECTOR = 0x08
    void High_ISR(void) {
        _asm goto SYS_InterruptHigh _endasm
    }
    #pragma code LOW_INTERRUPT_VECTOR = 0x18
    void Low_ISR(void) {
        _asm goto SYS_InterruptLow _endasm
    }
    #pragma code
    #pragma interrupt SYS_InterruptHigh
    void SYS_InterruptHigh() {
        //Check which interrupt flag caused the interrupt.
        //Service the interrupt
        //Clear the interrupt flag
        //Etc.
    #if defined(USB_INTERRUPT)
        USBDeviceTasks();
    #endif
    } //This return will be a "retfie fast", since this is in a #pragma interrupt section
    #pragma interruptlow SYS_InterruptLow
    void SYS_InterruptLow() {
        //Check which interrupt flag caused the interrupt.
        //Service the interrupt
        //Clear the interrupt flag
        //Etc.
    } //This return will be a "retfie", since this is in a #pragma interruptlow section


#elif defined(__XC8)                            // MCHP XC8 compiler
    void interrupt SYS_InterruptHigh() {
        //Check which interrupt flag caused the interrupt.
        //Service the interrupt
        //Clear the interrupt flag
        //Etc.
        volatile int tmp;
    #if defined(USB_INTERRUPT)
        USBDeviceTasks();
    #endif
/*        if (INTCONbits.INT0IF || INTCON3bits.INT1IF) {
            LED_STATUS = HIGH;
            delay_ms(5);
            LED_STATUS = LOW;
        }*/
        if (INTCONbits.TMR0IF) // If the external flag is 1, do .....
        {
            if (waiting_for_timer) {
				LED_STATUS = LOW;
                if (0 == --waiting_for_timer) {
    //                INTCONbits.TMR0IE = 0; //disable interrupt
                    num_quarter_hours_delay = 0;
                    need_tx_time_delay = 1;
                }
            }
			
			if (timeout_err > 0)
				timeout_err--;
			
            TMR0H = ONE_S_TMR0H;
            TMR0L = ONE_S_TMR0L;
            time_tick_flag = time_tick_flag ? 0 : 0x80;
            INTCONbits.TMR0IF = 0; // Reset the external interrupt flag
        }
        else if (INTCONbits.INT0IF || INTCON3bits.INT1IF) {
            LED_STATUS = HIGH;
            waiting_for_timer = TIME_CHANGE_SECONDS;

            if (INTCONbits.INT0IF) {
                show_interm = 1;
                if (button_interm_debounce == 0)
                    need_tx_interm_toggle = 1;
                button_interm_debounce=5;
            } else {
                if (button_next_debounce == 0 && num_quarter_hours_delay < 127) {
                    num_quarter_hours_delay++;
                    need_tx_time_delay = 1;                
                }
                
                button_next_debounce=15;
            }
            
            //reset interrupt flags
            INTCONbits.INT0IF = 0;
            INTCON3bits.INT1IF = 0;

            //timer0 interrupt enable
            TMR0H = ONE_S_TMR0H;
            TMR0L = ONE_S_TMR0L;
        }        
    } //This return will be a "retfie fast"
#else
  #error NO VALID COMPILER SELECTED !!!
#endif


/*********************************************************************
* Function: void SYSTEM_Initialize( SYSTEM_STATE state )
*
* Overview: Initializes the system.
*
* PreCondition: None
*
* Input:  SYSTEM_STATE - the state to initialize the system into
*
* Output: None
*
********************************************************************/
void SYSTEM_Initialize( SYSTEM_STATE state )
{
    switch(state)
    {
        case SYSTEM_STATE_USB_START:
            init_MCU();
        	init_MAX7219();            
            break;

        case SYSTEM_STATE_USB_SUSPEND:
            break;

        case SYSTEM_STATE_USB_RESUME:
            break;
    }
}


void delay_us(int x) {
	delayus_variable = (unsigned char) (x);
	asm("movlb (_delayus_variable) >> 8");
	asm("nop");
	asm("nop");
	asm("nop");
	asm("nop");
	asm("nop");
	asm("nop");
	asm("nop"); //asm("nop"); asm("nop"); asm("nop"); asm("nop"); 
	asm("decfsz (_delayus_variable)&0ffh,f");
	asm("goto $ - 16");
}

const char LOVE[] = "teiubesc";

void love()
{
	writeMAX7219_3(1, MAX7219_LETTERS[LOVE[0]-'a'], 1, 0, 1, 0);
	writeMAX7219_3(2, MAX7219_LETTERS[LOVE[1]-'a'], 2, 0, 2, 0);
	writeMAX7219_3(3, MAX7219_LETTERS[LOVE[2]-'a'], 3, 0, 3, 0);
	writeMAX7219_3(4, MAX7219_LETTERS[LOVE[3]-'a'], 4, 0, 4, 0);
	writeMAX7219_3(5, MAX7219_LETTERS[LOVE[4]-'a'], 5, 0, 5, 0);
	writeMAX7219_3(6, MAX7219_LETTERS[LOVE[5]-'a'], 6, 0, 6, 0);
	writeMAX7219_3(7, MAX7219_LETTERS[LOVE[6]-'a'], 7, 0, 7, 0);
	writeMAX7219_3(8, MAX7219_LETTERS[LOVE[7]-'a'], 8, 0, 8, 0);
	delay_ms(1000);
	writeMAX7219_3(1, 0, 1, MAX7219_LETTERS[LOVE[0]-'a'], 1, 0);
	writeMAX7219_3(2, 0, 2, MAX7219_LETTERS[LOVE[1]-'a'], 2, 0);
	writeMAX7219_3(3, 0, 3, MAX7219_LETTERS[LOVE[2]-'a'], 3, 0);
	writeMAX7219_3(4, 0, 4, MAX7219_LETTERS[LOVE[3]-'a'], 4, 0);
	writeMAX7219_3(5, 0, 5, MAX7219_LETTERS[LOVE[4]-'a'], 5, 0);
	writeMAX7219_3(6, 0, 6, MAX7219_LETTERS[LOVE[5]-'a'], 6, 0);
	writeMAX7219_3(7, 0, 7, MAX7219_LETTERS[LOVE[6]-'a'], 7, 0);
	writeMAX7219_3(8, 0, 8, MAX7219_LETTERS[LOVE[7]-'a'], 8, 0);
	delay_ms(1000);
	writeMAX7219_3(1, 0, 1, 0, 1, MAX7219_LETTERS[LOVE[0]-'a']);
	writeMAX7219_3(2, 0, 2, 0, 2, MAX7219_LETTERS[LOVE[1]-'a']);
	writeMAX7219_3(3, 0, 3, 0, 3, MAX7219_LETTERS[LOVE[2]-'a']);
	writeMAX7219_3(4, 0, 4, 0, 4, MAX7219_LETTERS[LOVE[3]-'a']);
	writeMAX7219_3(5, 0, 5, 0, 5, MAX7219_LETTERS[LOVE[4]-'a']);
	writeMAX7219_3(6, 0, 6, 0, 6, MAX7219_LETTERS[LOVE[5]-'a']);
	writeMAX7219_3(7, 0, 7, 0, 7, MAX7219_LETTERS[LOVE[6]-'a']);
	writeMAX7219_3(8, 0, 8, 0, 8, MAX7219_LETTERS[LOVE[7]-'a']);
	delay_ms(1000);
}

void transilien_new_data(const char* data) {
    memcpy(CURRENT_DATA, data, 36);	
	timeout_err = TIMEOUT_ERROR;
}

uint8_t transilien_get_tx_data(int8_t* command, int8_t* parameter) {
    //send time delay before dir_switch if both are needed
    //for no particular reason
    uint8_t ret = need_tx_time_delay | need_tx_dir_switch | need_tx_interm_toggle;
    if (need_tx_time_delay) {
        *command = CID_SET_SHIFT;
        *parameter = num_quarter_hours_delay;
        need_tx_time_delay = 0;
    } else if (need_tx_dir_switch) {
        *command = CID_SET_DIRECTION;
        *parameter = direction_bit;
        need_tx_dir_switch = 0;
    } else if (need_tx_interm_toggle) {
        *command = CID_SHOW_INTERM;
        *parameter = show_interm;
        need_tx_interm_toggle = 0;
    }
    return ret;
}

void process_train_time(int8_t train_idx, char* curdata, int8_t* display) {
    int data_idx = 4 + train_idx*8;
    if (curdata[data_idx+5] == 'S' && time_tick_flag) {
        display[0] = MAX7219_LETTERS['S' - 'A'];
        display[1] = MAX7219_LETTERS['U' - 'A'];
        display[2] = MAX7219_LETTERS['P' - 'A'];
        display[3] = MAX7219_LETTERS['P' - 'A'];
    } else if (curdata[data_idx+1] == '-' || timeout_err == 0) {
        display[0] = display[1] = display[2] = display[3] = MAX7219_DASH;
    } else {
        uint8_t rtflag = curdata[data_idx+5] == 'T' ? 0x80 : 0x00;
        
        display[0] = MAX7219_DIGITS[curdata[data_idx+1]-'0'] | rtflag;
        display[1] = MAX7219_DIGITS[curdata[data_idx+2]-'0'] | 0x80; //show dot
        display[2] = MAX7219_DIGITS[curdata[data_idx+3]-'0'] | rtflag;
        display[3] = MAX7219_DIGITS[curdata[data_idx+4]-'0'] | rtflag;
    }    
}

void process_global_time(char* timedata, int8_t* display) {
	if (timeout_err == 0) {
		display[0] = MAX7219_DASH;
		display[1] = MAX7219_LETTERS['e'-'a']; 
		display[2] = MAX7219_LETTERS['r'-'a'];
		display[3] = MAX7219_LETTERS['r'-'a'];		
	} else if (timedata[0] == '-') {
		display[0] = display[1] = display[2] = display[3] = MAX7219_DASH;
	} else if (timedata[0] == 'L') {
		display[0] = MAX7219_LETTERS['i'-'a'];
		display[1] = MAX7219_LETTERS['n'-'a'];
		display[2] = MAX7219_LETTERS['i'-'a'];
		display[3] = MAX7219_LETTERS['t'-'a'];
	} else if (timedata[0] == 'P') {
		display[0] = MAX7219_DASH;
		display[1] = MAX7219_LETTERS['p'-'a']; 
		display[2] = MAX7219_LETTERS['a'-'a'];
		display[3] = MAX7219_LETTERS['r'-'a'];
	} else if (timedata[0] == 'B') {
		display[0] = MAX7219_DASH;
		display[1] = MAX7219_LETTERS['t'-'a']; 
		display[2] = MAX7219_LETTERS['a'-'a'];
		display[3] = MAX7219_LETTERS['f'-'a'];
	} else {
        int8_t tick_flag = timedata[4+8*0+5]=='T' || timedata[4+8*1+5]=='T' || timedata[4+8*2+5]=='T' || timedata[4+8*3+5]=='T' ? 0x80 : time_tick_flag;
        
		display[0] = MAX7219_DIGITS[timedata[ 0]-'0'];
		display[1] = MAX7219_DIGITS[timedata[ 1]-'0']|tick_flag;
		display[2] = MAX7219_DIGITS[timedata[ 2]-'0'];
		display[3] = MAX7219_DIGITS[timedata[ 3]-'0'];
	}
}

uint8_t process_train_id(int8_t train_id, int8_t corresp_info) {
    if (show_interm) {
        if (corresp_info == '-') 
            return MAX7219_DASH;
        else if (corresp_info == 'Z')
            return MAX7219_LETTERS['T' - 'A'];
        else
            return MAX7219_DIGITS[corresp_info - '0'];
    } else {
        if (train_id == '-' || train_id == 'X')
            return MAX7219_DASH;
        else
            return MAX7219_LETTERS[train_id-'A'];
    }
}

void transilien_main_update() {
	int data_src = 0, j;

	//MAX1: train times 1 [dig 1..4] ,2 [dig 5..8] 
	//MAX2: current time [dig 1..4] , train names 1..4 [dig 5..8]
	//MAX3: train times 3 [dig 1..4] ,4 [dig 5..8]

    if (button_next_debounce > 0) {
        button_next_debounce--;
    }
    
    if (button_interm_debounce > 0) {        
        if (PIN_PUSH_INTERM == LOW)
            button_interm_debounce = 5;
        else {
            button_interm_debounce--;        
            if (button_interm_debounce == 0) {
                show_interm = 0;
                need_tx_interm_toggle = 1;
            }
        }
    }
    
    char* curdata = CURRENT_DATA;
    // get 1st digit of j

////FORMAT: CURTIME:TIMECODE-{TRAINNAME:CHAR-ARRIVE:TIMECODE-STATUS:CHAR[0HRS]-CORRESP:CHAR-UNUSED:CHAR}x4    
/* 
0: 3 1350
4 :11 D1359R72
12:19 H1410S55
20:27 D1411H32
28:35 H1415SZ0";
 STATUS:
 *  0 - ok, real-time
 *  H - from timetable
 *  R - delayed
 *  S - canceled
 */
    
    int8_t t1[4], t2[4], t3[4], t4[4], tg[4];
    process_train_time(0, curdata, t1);
    process_train_time(1, curdata, t2);
    process_train_time(2, curdata, t3);
    process_train_time(3, curdata, t4);

	process_global_time(curdata, tg);
	
    writeMAX7219_3(1, t1[0], 1, tg[0], 1, t4[0]);
    writeMAX7219_3(2, t1[1], 2, tg[1], 2, t4[1]);
    writeMAX7219_3(3, t1[2], 3, tg[2], 3, t4[2]);
    writeMAX7219_3(4, t1[3], 4, tg[3], 4, t4[3]);
    writeMAX7219_3(5, t2[0], 5, process_train_id(curdata[ 4], curdata[10]), 5, t3[0]);
    writeMAX7219_3(6, t2[1], 6, process_train_id(curdata[12], curdata[18]), 6, t3[1]);
    writeMAX7219_3(7, t2[2], 7, process_train_id(curdata[20], curdata[26]), 7, t3[2]);
    writeMAX7219_3(8, t2[3], 8, process_train_id(curdata[28], curdata[34]), 8, t3[3]);

    DATA_bit = LOW;
   
    j = PIN_DIRECTION;
    if (j != direction_bit) {
		
		if (j == 0)
			memcpy(CURRENT_DATA, DATA_PARI, 36);		
		else
			memcpy(CURRENT_DATA, DATA_BANL, 36);
		
        LED_STATUS = HIGH;
        waiting_for_timer = TIME_CHANGE_SECONDS;
		
        direction_bit = j;
        need_tx_dir_switch = 1;
    }
    
    data_src = data_src + 1;
    delay_ms(20);
    
    main_counter++;
} //end main

// shift data to MAX7219
// Rb7 -> SERCLK, Rb6 -> DATA_bit, Rb5 -> CS not

void ssrOut(unsigned char val) {
	int j;
	for (j = 1; j <= 8; j++) { // shift out MSB first
		unsigned char temp = val & 0x80; // MSB out first
		SERCLK = LOW;
		if (temp == 0x80)
			DATA_bit = HIGH; // Rb6 DATA          
		else
			DATA_bit = LOW;
		SERCLK = HIGH;
		val = val << 1; // shift one place left
	} 
}

void writeMAX7219_part(char address, char data) {
	if ((address < 1) || (address > 8)) return;
	ssrOut(address); // valid numbers 1-8
	ssrOut(data);
}

void writeMAX7219_3(char address1, char data1, char address2, char data2, char address3, char data3) {
	writeMAX7219_part(address1, data1);
	writeMAX7219_part(address2, data2);
	writeMAX7219_part(address3, data3);
	pulseCS();
}

void writeMAX7219(char address, char data) {
	if ((address < 1) || (address > 8)) return;
	ssrOut(address); // valid numbers 1-8
	ssrOut(data);
	pulseCS();
}

void pulseCS(void) {
	CS = HIGH;
	delay_us(5);
	CS = LOW;
}

void init_MAX7219(void) {
	int i, k;
	CS = LOW; // CS NOT

		// set decode mode
	for (i = 0; i < NUM_MAX7219; ++i) {
		ssrOut(0x09); // address
		ssrOut(0x00); // binary input, no BCD
	}
	pulseCS();

	for (i = 0; i < NUM_MAX7219; ++i) {
		// set intensity
		ssrOut(0x0A); // address
		ssrOut(0x0D); // 5/32s
	}
	pulseCS();

	for (i = 0; i < NUM_MAX7219; ++i) {
		// set scan limit 0-7
		ssrOut(0x0B); // address
		ssrOut(0x07); // 8 digits
		//ssrOut(0x03); // 4 digits
	}
	pulseCS();

	// clear MAX7219 all zeros
/*	for (i = 1; i <= 8; i++) {
		for (k = 0; k < NUM_MAX7219; ++k) {
			ssrOut(i);
			ssrOut(0x00);
		}
		pulseCS();
	}*/

	for (i = 0; i < NUM_MAX7219; ++i) {
		// set for DISPLAY test
		ssrOut(0x0f); // address
		ssrOut(0x01); // On
	}
	pulseCS();

	//out of shutdown mode
	for (i = 0; i < NUM_MAX7219; ++i) {
		// set for normal operation
		ssrOut(0x0C); // address
		ssrOut(0x01); // On
	}
	pulseCS();
	delay_ms(1000);

	for (i = 0; i < NUM_MAX7219; ++i) {
		// set for DISPLAY test
		ssrOut(0x0f); // address
		ssrOut(0x00); // Off
	}
	pulseCS();
	delay_ms(50);
}

void delay_ms(int i) {
	long int j;
	for (j = 0; j < i; ++j) {
		delay_us(1000);
	}
}

//Ports initialized etc.

void init_MCU(void) {
	// disables converters A/D	
	ADCON0bits.ADON = 0;
	ADCON1 = 0x0F;

	//all RA pins are output
	LATA = 0;
	PORTA = 0;
	TRISA = 0;

	//PORTB are outputs, except RB2,RB1,RB0 are inputs
	TRISB = 0b00000111;
	PORTB = 0b00000000;
    
	//Rc0,Rc1 are inputs (MICRO SWITCHES)
	TRISC = 0;
    TRISD = 0;
	
	LED_STATUS = LOW;
    
	//interrupt configuration
	//select pull-up resistors on port B (Rb4...Rb7).
	INTCONbits.INT0E = 1; //enable Interrupt 0 (RB0 as interrupt)
	INTCON2bits.INTEDG0 = 0; //cause interrupt at falling edge
	INTCONbits.INT0F = 0; //reset interrupt flag

	INTCON3bits.INT1E = 1; //enable Interrupt 1 (RB1 as interrupt)
	INTCON2bits.INTEDG1 = 0; //cause interrupt at falling edge
	INTCON3bits.INT1F = 0; //reset interrupt flag

	//INTCON3bits.INT2E = 0; //enable Interrupt 1 (RB1 as interrupt)
	//INTCON3bits.INT2F = 1; //reset interrupt flag
    
    //INTCONbits.RBIE = 1;
    //INTCON2bits.RBIP = 1;
    INTCON2bits.TMR0IP = 1;
    
	//timer 0 configuration
	T0CONbits.T08BIT = 0;
	T0CONbits.T0CS = 0;
	T0CONbits.PSA = 0;
	T0CONbits.T0PS2 = 1;
	T0CONbits.T0PS1 = 1;
	T0CONbits.T0PS0 = 0;
	TMR0H = ONE_S_TMR0H;
	TMR0L = ONE_S_TMR0L;
	T0CONbits.TMR0ON = 1;
    INTCONbits.TMR0IE = 1;
		
    INTCON2bits.RBPU = 0;
    
	ei();
	
	OSCCONbits.SCS = 0b00;
	OSCCONbits.IRCF0 = 1; //set to 8MHz
	OSCCONbits.IRCF1 = 1; //set to 8MHz
	OSCCONbits.IRCF2 = 1; //set to 8MHz
	OSCTUNEbits.INTSRC = 0;

	UCFGbits.UPUEN = 1;
	UCFGbits.UTRDIS = 0;
	UCFGbits.FSEN = 1;
	UCONbits.USBEN = 1;
	
    INTCONbits.GIEL = 1;
    
    direction_bit = PIN_DIRECTION;
    
    transilien_new_data(DATA_LOAD);
}

void delay_1s(void) {
	int k;
	for (k = 0; k < 1000; ++k)
		delay_us(1000);
}