import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.File;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.io.IOException;

public class ImageEditor {

    static BufferedImage image;

    public static void main(String[] args) {

        JFrame frame = new JFrame("Image Editor");

        frame.setSize(800, 600);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        

        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 10, 10));
        
        JButton Open_button = new JButton("Открыть");
        JButton Change_button = new JButton("Обработать");
        JButton Save_button = new JButton("Сохранить");
        
        buttonPanel.add(Open_button);
        buttonPanel.add(Change_button);
        buttonPanel.add(Save_button);

        
        ImageIcon imageIcon = new ImageIcon("sample.png"); 
        JLabel imageLabel = new JLabel(imageIcon);
        
        
        imageLabel.setHorizontalAlignment(SwingConstants.CENTER);
        imageLabel.setVerticalAlignment(SwingConstants.CENTER);

        
        imageLabel.setBorder(BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1));

        
        frame.add(buttonPanel, BorderLayout.NORTH); 
        frame.add(imageLabel, BorderLayout.CENTER);  

        
        Open_button.addActionListener(new ActionListener(){
            @Override
            public void actionPerformed(ActionEvent e) {
            if(e.getSource() == Open_button){
                JFileChooser fileChooser = new JFileChooser();
                int response = fileChooser.showOpenDialog(null);

                if(response == JFileChooser.APPROVE_OPTION){
                File file = fileChooser.getSelectedFile();
                try{
                    image = ImageIO.read(file);
                    imageLabel.setIcon(new ImageIcon(image));
                }
                catch (IOException ex) {
                    ex.printStackTrace();
                }
                
            }
            }
        }
        });

        Change_button.addActionListener(new ActionListener(){
            @Override
            public void actionPerformed(ActionEvent e) {
                if (image != null) {
                image.setRGB(0, 0, new Color(0, 64, 64).getRGB());
                image.setRGB(0, (image.getHeight() / 2), new Color(64, 64, 64).getRGB());
                image.setRGB(image.getWidth() - 1, image.getHeight() - 1, new Color(127, 127, 64).getRGB());
                
                imageLabel.setIcon(new ImageIcon(image));
                }
            }
        });

        Save_button.addActionListener(new ActionListener(){
            @Override
            public void actionPerformed(ActionEvent e) {
                JFileChooser fileChooser = new JFileChooser();
                int response = fileChooser.showSaveDialog(null);

                if (response == JFileChooser.APPROVE_OPTION) {
                    File file = fileChooser.getSelectedFile();

                    try {
                        ImageIO.write(image, "png", file);
                    } catch (IOException ex) {
                        ex.printStackTrace();
                    }
                }
            }
        });

    
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }
}