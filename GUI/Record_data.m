clc
clear

bitToVolts = 1 ; %single(3.3/4095);
numSamples = single(40000); % Number of samples to read

s = serialport("COM3", 460800);
flush(s); % Remove old data from usb buffer

saveData = zeros(numSamples,1,'uint16');

disp('Looking for header...')

isSynced = false;
while ~isSynced
    if s.NumBytesAvailable >= 1
        b1 = read(s, 1, "uint8"); %läs en byte i taget

        if b1 == 0x80 % första halvan av headern

            while s.NumBytesAvailable < 1
                pause(1E-6)
            end
            b2 = read(s, 1, "uint8");

            if b2 == 0x80 %andra halvan av headern
                isSynced = true;
                disp('Syncing done, starting recording!')
            end
        end
    end
end

                
% fig = figure(1);
% ax = axes('Parent', fig);
% graph = animatedline('Color','b','LineWidth',2);
% ax.YGrid = 'on';
% ax.XGrid = 'on';
header_counter = 1;
for k = 2:numSamples
    while s.NumBytesAvailable < 2 % data is sent in 1 byte package, so we need to collect 2 packages for 12 bit
        pause(1E-6); %to not kill cpu
    end

    raw = read(s, 2, "uint8"); % Read 2 bytes
    value = uint16(raw(1) + raw(2)*256);
    %data = typecast(uint8(raw), 'uint16'); % Convert to uint16
    saveData(k) = uint16(raw(1) + raw(2)*256);
    if value == 32896
       header_counter = header_counter + 1 ;
    end
    % addpoints(graph,k,cast(saveData(k),'single').*bitToVolts);
    % ax.XLim = [max(0,k-100) k+10]; % Update axis limits for scrolling effect
    
    %drawnow limitrate % forces new frame allways after 50 ms
end

save('EMGData_wrist_rest.mat', 'saveData');
disp('Done')
disp(header_counter)
disp('data:')
subset = saveData(end-200:end);
disp(subset)