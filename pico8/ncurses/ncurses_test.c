#include <ncurses.h>
#include <stdlib.h>
#include <unistd.h>


// need export TERM=xterm-256color

// perl -pe 's!^\s*(\d+)\s+(\d+)\s+(\d+).*$!\e[38;2;$1;$2;$3m$&\e[m!' /usr/share/X11/rgb.txt

// clear:
// echo -e \\x1b\\x5b\\x33\\x4a\\x1b\\x5b\\x48\\x1b\\x5b\\x32\\x4a
// \33[3J\33[H\33[2J
// \\x1b[3J\\x1b[H\\x1b[2J

// ESC [ 3 J   - clear buffer (but it doesn't)
// ESC [ H    - move to top
// ESC [ 2 J  - clear screen

// initscr -

//   \\x1b\\x5b\\x3f\\x31\\x30\\x34\\x39\\x68\\x1b\\x5b\\x31\\x3b\\x32\\x34\\x72\\x1b\\x28\\x42\\x1b\\x5b\\x6d\\x1b\\x5b\\x34\\x6c\\x1b\\x5b\\x3f\\x37\\x68\\x1b\\x5b\\x48\\x1b\\x5b\\x32\\x4a

//   \x1b\x5b\x3f\x31\x30\x34\x39\x68 
//   \x1b\x5b\x31\x3b\x32\x34\x72 
//   \x1b\x28\x42 
//   \x1b\x5b\x6d
//   \x1b\x5b\x34\x6c
//   \x1b\x5b\x3f\x37\x68\x1b\x5b\x48\x1b\x5b\x32\x4a

// \x1b[?1049h  - alt screen buffer
// \x1b[1;24r   - Set Scrolling Region [top;bottom]
// \x1b(B       - ??
// \x1b[m       - reset color
// \x1b[4l      - replace mode ?
// \x1b[?7h     - Wraparound Mode
// \x1b[H       - cursor to 1,1
// \x1b[2J      - clear

// endwin
// \x1b\x5b\x32\x34\x3b\x31\x48
// \x1b\x5b\x3f\x31\x30\x34\x39\x6c 
// \x0d
// \x1b\x5b\x3f\x31\x6c
// \x1b\x3e

// ESC[24;1H   - reposition cursor
// ESC[?1049l  - back to normal screen buffer
// ^M          - CR
// ESC[?1l     - normal cursor keys
// ESC>        - Exit alternate keypad mode.


// lots of codes https://www.xfree86.org/current/ctlseqs.html  https://en.wikipedia.org/wiki/ANSI_escape_code


int main()
{	
	//for(int i = 128; i < 256; ++i) {
		printf("\x1b[38;2;%d;%d;%dm %d: \u2580\n", 200, 200, 100);
		//putchar(2580);
	//}
	return 0;

    int ch;
	initscr();
	if(has_colors() == FALSE)
	{	
		endwin();
		printf("Your terminal does not support color\n");
		exit(1);
	}
	start_color();
	cbreak();
	keypad(stdscr, TRUE);
	noecho();

    printw("can change:%d, colors:%d pairs:%d", can_change_color(), COLORS, COLOR_PAIRS);

	char* buf = malloc(10000);
	int offset = 0;

	offset += sprintf(buf + offset, "\x1b[H"); // move to 1,1
	//int count = sprintf(buf, "\x1b[48;2;200;200;100m \x1b[48;2;100;200;100m ");

	move(0, 0);
	refresh();
	//write(1, buf, count);
	//printf(buf);

	//int idx = 1;
	for(int y = 0; y < 64; ++y)
	{
		for(int x = 0; x < 64; ++x)
		{
			offset += sprintf(buf + offset, "\x1b[48;2;%d;%d;%dm ", x*4, y*4, 200);
		}
		offset += sprintf(buf + offset, "\x1b[%dH", y+1);
	}

	write(1, buf, offset);	

	ch = getch();
	endwin();

	return 0;
}